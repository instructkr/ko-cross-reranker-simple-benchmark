import numpy as np
from FlagEmbedding import LayerWiseFlagLLMReranker
from .base import BaseReranker


class LayerWiseFlagLLMRerankerType(BaseReranker):
    def __init__(
        self,
        model_path: str = "BAAI/bge-reranker-v2-minicpm-layerwise",
        use_fp16: bool = True,
        use_bf16: bool = False,
        devices: list[str] = None,
        cache_dir: str | None = None,
        apply_minmax_normalize: bool = False,
    ):
        """
        :param model_path: Name/path of the model on HF Hub
               (e.g. 'BAAI/bge-reranker-v2-minicpm-layerwise').
        :param use_fp16: Whether to load/run the model with FP16 (speeds up inference).
        :param use_bf16: Whether to load/run the model with BF16.
                         (Set one of use_fp16/use_bf16 to True)
        :param devices: List of devices, e.g. ["cpu"] or ["cuda:0"]. Default None -> CPU
        :param cache_dir: Optional cache directory for model files.
        :param apply_minmax_normalize: Whether to apply min-max normalization on final scores.
        """
        self.apply_minmax_normalize = apply_minmax_normalize

        self.reranker = LayerWiseFlagLLMReranker(
            model_path,
            use_fp16=use_fp16,
            use_bf16=use_bf16,
            cache_dir=cache_dir,
        )

    def compute_score(
        self,
        pairs: list[tuple[str, str]],
        normalize: bool = True,
        cutoff_layers: list[int] = None,
    ) -> list[float]:
        """
        Compute scores for each (query, doc_text) pair.

        :param pairs: list of (query, doc_text) pairs.
        :param normalize: Whether to apply min-max normalization on the raw scores.
        :param cutoff_layers: Optional layers to 'cut off' in the forward pass (layerwise).
        :return: list of float scores, one per (query, doc) pair.
        """
        # Convert (q, d) -> [q, d]
        input_pairs = [list(p) for p in pairs]

        # LayerWiseFlagLLMReranker는 compress_ratio, compress_layers 등을 받지 않으므로 제거.
        # cutoff_layers만 필요한 경우 전달 가능.
        scores = self.reranker.compute_score(
            input_pairs,
            cutoff_layers=cutoff_layers,
        )

        if normalize or self.apply_minmax_normalize:
            # Optional min-max normalization
            min_score = float(np.min(scores))
            max_score = float(np.max(scores))
            if (max_score - min_score) > 1e-8:
                scores = [(s - min_score) / (max_score - min_score) for s in scores]
            else:
                scores = [0.0 for _ in scores]

        return scores

    def compute_score_batch(
        self,
        query: str,
        docs: list[str],
        normalize: bool = False,
        cutoff_layers: list[int] = None,
    ) -> list[float]:
        """
        Batch version to accept a single query + multiple docs.

        :param query: A single query string.
        :param docs: list of doc_texts.
        :param normalize: Whether to apply min-max normalization across these scores.
        :param cutoff_layers: Optional layers to 'cut off' in the forward pass.
        :return: list of float scores, one per doc in 'docs'.
        """
        # Build list of [query, doc]
        input_pairs = [[query, doc] for doc in docs]

        scores = self.reranker.compute_score(
            input_pairs,
            cutoff_layers=cutoff_layers,
        )

        if normalize or self.apply_minmax_normalize:
            min_score = float(np.min(scores))
            max_score = float(np.max(scores))
            if (max_score - min_score) > 1e-8:
                scores = [(s - min_score) / (max_score - min_score) for s in scores]
            else:
                scores = [0.0 for _ in scores]

        return scores
