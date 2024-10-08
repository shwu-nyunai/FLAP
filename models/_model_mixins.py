import typing as tp
from transformers import logging, PretrainedConfig
import torch

logger = logging.get_logger(__name__)


def repeat_list_or_single_element(n: int, x: tp.Any) -> tp.List[tp.Any]:
    if isinstance(x, tp.Iterable):
        if not len(x) == n:
            raise ValueError(
                f"Length of {x} is not equal to the number of hidden layers {n}"
            )
        return x
    return [x] * n


class PrunedConfigMixin:
    def __post_init__(self, **kwargs):
        pruning_config: tp.Dict[str, tp.Any] = kwargs.get("pruning_config", None)
        if pruning_config:
            logger.info(f"Loading config for a pruned model.")
            self.mlp_bias = pruning_config.get("mlp_bias", False)
            self.attention_bias = pruning_config.get("attention_bias", False)
            self.first_pruned_layer_idx = pruning_config.get(
                "first_pruned_layer_idx", 1e9
            )
            self.num_hidden_layers = pruning_config.get(
                "num_hidden_layers", self.num_hidden_layers
            )
            self.intermediate_size = repeat_list_or_single_element(
                self.num_hidden_layers,
                pruning_config.pop("intermediate_size", self.intermediate_size),
            )
            self.num_attention_heads = repeat_list_or_single_element(
                self.num_hidden_layers,
                pruning_config.pop("num_attention_heads", self.num_attention_heads),
            )
            self.num_key_value_heads = repeat_list_or_single_element(
                self.num_hidden_layers,
                pruning_config.pop("num_key_value_heads", self.num_key_value_heads),
            )
            self.pruning_config = pruning_config
        else:
            self.mlp_bias = kwargs.get("mlp_bias", False)
            self.attention_bias = kwargs.get("attention_bias", False)
            self.first_pruned_layer_idx = kwargs.get("first_pruned_layer_idx", 1e9)
            self.intermediate_size = repeat_list_or_single_element(
                self.num_hidden_layers, self.intermediate_size
            )
            self.num_attention_heads = repeat_list_or_single_element(
                self.num_hidden_layers, self.num_attention_heads
            )
            self.num_key_value_heads = repeat_list_or_single_element(
                self.num_hidden_layers, self.num_key_value_heads
            )


class BaseMLP(torch.nn.Module):
    def __init__(self, config: PretrainedConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx

    def _patch_mlp_init(self):
        """Extends MLP module initialization to a pruned model."""
        self.intermediate_size = self.config.intermediate_size[self.layer_idx]


class PrunedAttentionMixin:
    """Mixin class to adapt attention mechanism for pruned models."""

    def _patch_attention_init(self):
        """Extends attention module initialization to a pruned model."""
        self.num_key_value_heads = self.config.num_key_value_heads[self.layer_idx]
        self.num_heads = self.config.num_attention_heads[self.layer_idx]
        self.head_dim = 128
