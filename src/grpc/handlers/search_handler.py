"""gRPC handler for SearchService."""

import logging

import grpc

from src.config import Config
from src import search_pb2
from src import search_pb2_grpc

logger = logging.getLogger(__name__)


class SearchHandler(search_pb2_grpc.SearchServiceServicer):
    """Stub implementation of the SearchService."""

    def __init__(self, config: Config) -> None:
        self._config = config

    async def SearchProperties(
        self,
        request: search_pb2.SearchRequest,
        context: grpc.aio.ServicerContext,
    ) -> search_pb2.SearchResponse:
        """Search for properties using natural language."""
        try:
            if not request.query:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "query is required",
                )
            if not request.tenant_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "tenant_id is required",
                )

            logger.info(
                "SearchProperties: tenant_id=%s query_len=%d request_id=%s",
                request.tenant_id,
                len(request.query),
                request.request_id,
            )

            return search_pb2.SearchResponse(
                request_id=request.request_id,
                results=[],
                suggested_refinements=[],
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("SearchProperties failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def GetSearchSuggestions(
        self,
        request: search_pb2.SuggestionRequest,
        context: grpc.aio.ServicerContext,
    ) -> search_pb2.SuggestionResponse:
        """Get autocomplete suggestions for a partial query."""
        try:
            if not request.partial_query:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "partial_query is required",
                )

            logger.info(
                "GetSearchSuggestions: partial_query=%s request_id=%s",
                request.partial_query,
                request.request_id,
            )

            return search_pb2.SuggestionResponse(
                request_id=request.request_id,
                suggestions=[],
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("GetSearchSuggestions failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
