import os
import typing
from pathlib import Path

from binaryninja import (
    BinaryView,
    show_message_box,
    MessageBoxButtonSet,
    MessageBoxIcon,
    HighlightStandardColor,
    HighlightColor,
    Architecture,
)
from manticore.core.plugin import StateDescriptor


class MUIState:
    def __init__(self, bv: BinaryView):
        self.bv = bv
        self.states: typing.Dict[int, StateDescriptor] = {}
        self.state_change_listeners: typing.List[
            typing.Callable[
                [typing.Dict[int, StateDescriptor], typing.Dict[int, StateDescriptor]], None
            ]
        ] = []

    def get_state(self, state_id: int) -> typing.Optional[StateDescriptor]:
        """Get the state descriptor for a given id"""
        if state_id in self.states:
            return self.states[state_id]
        else:
            return None

    def get_state_address(self, state_id: int) -> typing.Optional[int]:
        """Get the current instruction address of a given state"""
        state = self.get_state(state_id)

        if state is None:
            return None

        if is_evm(self.bv):
            # get evm addr
            if state.pc is not None and isinstance(state.pc[-1], int):
                return state.pc[-1]
            else:
                return None
        else:
            # get native addr
            if isinstance(state.pc, int):
                return state.pc
            elif isinstance(state.last_pc, int):
                # use last_pc as a fallback
                return state.last_pc
            else:
                return None

    def navigate_to_state(self, state_id: int) -> None:
        """Navigate to the current instruction of a given state"""
        addr = self.get_state_address(state_id)

        if addr is not None:
            self.bv.navigate(self.bv.view, addr)
        else:
            show_message_box(
                "[MUI] No instruction information available",
                f"State {state_id} doesn't contain any instruction information.",
                MessageBoxButtonSet.OKButtonSet,
                MessageBoxIcon.ErrorIcon,
            )

    def on_state_change(
        self,
        callback: typing.Callable[
            [typing.Dict[int, StateDescriptor], typing.Dict[int, StateDescriptor]], None
        ],
    ) -> None:
        """Register an event listener for state changes"""
        self.state_change_listeners.append(callback)

    def notify_states_changed(self, new_states: typing.Dict[int, StateDescriptor]) -> None:
        """Updates internal states and invokes listeners"""
        old_states = self.states

        for callback in self.state_change_listeners:
            callback(old_states, new_states)

        self.states = new_states


def highlight_instr(bv: BinaryView, addr: int, color: HighlightStandardColor) -> None:
    """Highlight instruction at a given address"""
    blocks = bv.get_basic_blocks_at(addr)
    for block in blocks:
        block.set_auto_highlight(HighlightColor(color, alpha=128))
        block.function.set_auto_instr_highlight(addr, color)


def clear_highlight(bv: BinaryView, addr: int) -> None:
    """Remove instruction highlight"""
    blocks = bv.get_basic_blocks_at(addr)
    for block in blocks:
        block.set_auto_highlight(HighlightColor(HighlightStandardColor.NoHighlightColor))
        block.function.set_auto_instr_highlight(addr, HighlightStandardColor.NoHighlightColor)


def get_default_solc_path():
    """Attempt to find the path for the solc binary"""

    possible_paths = [Path(x) for x in os.environ["PATH"].split(":")]
    possible_paths.extend([Path(os.path.expanduser("~"), ".local/bin").resolve()])

    for path in possible_paths:
        if Path(path, "solc").is_file():
            return str(Path(path, "solc"))

    return ""


def is_evm(bv: BinaryView) -> bool:
    """Check if the current project arch is EVM"""

    return (
        "EVM" in [x.name for x in list(Architecture)]
        and bv.arch == Architecture["EVM"]
        and bv.session_data.mui_evm_source is not None
    )
