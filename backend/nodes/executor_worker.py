import asyncio
from backend.config import CHAR_LIMIT
from backend.tools.pdf_tools import pdf_parser, document_retriever
from backend.tools.audio_tools import transcribe_audio
from backend.tools.image_tools import image_analyser
from backend.tools.web_tools import web_search
from backend.tools.summarizer import map_reduce_summarizer


async def executor_worker_node(state: dict) -> dict:
    """
    Processes exactly ONE action asynchronously.
    Receives a single action dict + query from dispatcher via Send.
    Returns extracted_contents and urls_found for that one action.
    """
    action = state["action"]
    query = state["query"]
    user_id = state["user_id"] 
    action_id = action["action_id"]
    worker = action["worker"]
    operation = action["operation"]
    file_path = action.get("file_path")

    def make_error(msg):
        return {
            "extracted_contents": {"files": {action_id: {"error": msg}}},
            "urls_found": []
        }

    if worker in ["pdf_worker", "audio_worker", "image_worker"] and not file_path:
        return make_error(f"File path not provided for {worker}")

    try:

        # ---------------------------------
        # PDF WORKER
        # ---------------------------------
        if worker == "pdf_worker":
            pdf_result = await pdf_parser(file_path)

            if not pdf_result["success"]:
                return make_error(pdf_result["error"])

            urls = pdf_result.get("urls", [])

            if operation == "full_document":
                raw_content = pdf_result["content"]

                if len(raw_content) > CHAR_LIMIT:
                    summary_result = await map_reduce_summarizer(
                        text=raw_content,
                        source_type="pdf"
                    )
                    content_to_store = summary_result["summary"] if summary_result["success"] else raw_content[:CHAR_LIMIT]
                    was_summarized = summary_result.get("success", False)
                else:
                    content_to_store = raw_content
                    was_summarized = False

                return {
                    "extracted_contents": {"files": {action_id: {
                        "type": "pdf",
                        "content": content_to_store,
                        "was_summarized": was_summarized,
                        "urls": urls
                    }}},
                    "urls_found": urls
                }

            elif operation == "retrieve":
                retrieval_result = await document_retriever(
                    document_content=pdf_result["content"],
                    file_name=pdf_result["file_name"],
                    query=action.get("query") or query,
                    user_id=user_id
                )

                if retrieval_result["success"]:
                    return {
                        "extracted_contents": {"files": {action_id: {
                            "type": "pdf",
                            "retrieved_context": retrieval_result["retrieved_context"],
                            "urls": urls
                        }}},
                        "urls_found": urls
                    }
                else:
                    return make_error(retrieval_result["error"])

        # ---------------------------------
        # AUDIO WORKER
        # ---------------------------------
        elif worker == "audio_worker":
            result = await transcribe_audio(file_path)

            if result["success"]:
                raw_transcript = result["transcript"]

                if len(raw_transcript) > CHAR_LIMIT:
                    summary_result = await map_reduce_summarizer(
                        text=raw_transcript,
                        source_type="audio"
                    )
                    transcript_to_store = summary_result["summary"] if summary_result["success"] else raw_transcript[:CHAR_LIMIT]
                    was_summarized = summary_result.get("success", False)
                else:
                    transcript_to_store = raw_transcript
                    was_summarized = False

                return {
                    "extracted_contents": {"files": {action_id: {
                        "type": "audio",
                        "transcript": transcript_to_store,
                        "was_summarized": was_summarized
                    }}},
                    "urls_found": []
                }
            else:
                return make_error(result["error"])

        # ---------------------------------
        # IMAGE WORKER
        # ---------------------------------
        elif worker == "image_worker":
            result = await image_analyser(file_path=file_path, query=query)

            if result["success"]:
                return {
                    "extracted_contents": {"files": {action_id: {
                        "type": "image",
                        "analysis": result["analysis"]
                    }}},
                    "urls_found": []
                }
            else:
                return make_error(result["error"])

        # ---------------------------------
        # WEB WORKER
        # ---------------------------------
        elif worker == "web_worker":
            result = await web_search(query=action.get("query") or query)

            if result["success"]:
                return {
                    "extracted_contents": {"files": {action_id: {
                        "type": "web",
                        "content": str(result["results"])
                    }}},
                    "urls_found": []
                }
            else:
                return make_error(result["error"])

        return make_error(f"Unknown worker: {worker}")

    except Exception as e:
        return make_error(str(e))