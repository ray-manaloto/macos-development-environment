"""Installation modules for MDE tools and stacks."""

from mde.install.aws_k8s import install_aws_k8s_tools
from mde.install.tmux import install_tmux

__all__ = ["install_aws_k8s_tools", "install_tmux"]
