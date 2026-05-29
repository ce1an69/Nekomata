"""Interpretation, follow-up, fullscreen, copy/export for DrawScreen."""

from __future__ import annotations

import asyncio
import os

from rich.console import Group
from rich.markdown import Markdown
from rich.rule import Rule
from rich.text import Text

from textual.css.scalar import ScalarOffset
from textual.css.query import NoMatches
from textual.events import Key
from textual.geometry import Offset
from textual.widgets import Input

from nekomata.clipboard import copy_image as _copy_image_to_clipboard
from nekomata.clipboard import copy_text as _copy_text_to_clipboard
from nekomata.i18n import lazy_section
from nekomata.render.image_export import render_interp_image, save_image as _save_tmp_image
from nekomata.render.styles import C_LAVENDER, C_MAUVE, C_OVERLAY0, C_TEXT, EASE, EASE_SPRING
from nekomata.screens.draw_widgets import ConfirmExitInterpretation, SpreadSlot
from nekomata.screens.widgets import go_home

_STR = lazy_section("draw")


class InterpretMixin:
    """Interpretation, follow-up, fullscreen, and copy/export methods."""

    # -- StreamHandler callbacks --

    def _on_stream_render(self, parts) -> None:
        if parts is None:
            self._w_interp_content.update("")
        elif self._followup_active and self._prev_interp_content:
            combined = [
                Markdown(self._prev_interp_content, style=C_TEXT),
                Rule(style=C_MAUVE),
                Text(self._followup_question, style=C_LAVENDER),
                Rule(style=C_MAUVE),
            ]
            combined.extend(parts)
            self._w_interp_content.update(Group(*combined))
        else:
            self._w_interp_content.update(Group(*parts))

    def _on_stream_hints(self, text) -> None:
        self._w_interp_hints.update(text)

    def _on_stream_scroll(self) -> None:
        try:
            self._w_interp.scroll_end(animate=False)
        except NoMatches:
            pass

    def _on_stream_error(self, message: str, config_error: bool = False) -> None:
        self._dialog.show_error(
            message,
            self._update_phase_ui,
            sync_layout=self._sync_interp_layout,
            fit_height=lambda: self._dialog.fit_height(
                self._w_main_area, self._detail.visible
            ),
        )
        if config_error:
            from nekomata.screens.setup import SetupScreen

            app = self.app
            go_home(self)
            app.push_screen(SetupScreen(app.config))

    def _on_stream_done(self) -> None:
        new_content = "".join(self._stream._content_chars)

        if self._followup_active:
            self._prev_interp_content += (
                f"\n\n---\n\n> {self._followup_question}\n\n---\n\n{new_content}"
            )
            self._followup_active = False
            self._w_interp_content.update(
                Markdown(self._prev_interp_content, style=C_TEXT)
            )
            self._messages_history.append({"role": "assistant", "content": new_content})
        else:
            self._prev_interp_content = new_content
            self._initial_interp_content = new_content
            self._messages_history = list(self._stream.messages) + [
                {"role": "assistant", "content": new_content}
            ]
            self._first_interp_done = True

        self._dialog._streaming = False
        self._update_followup_hints()

        if self._followup_remaining > 0 and self._dialog.is_visible:
            self._show_followup()

    @property
    def _loading_timer(self):
        return self._stream._loading_timer

    @property
    def _stream_timer(self):
        return self._stream._timer

    # -- Box change / hints sync --

    def _on_box_changed(self) -> None:
        if self._box.active_box == "interp":
            self._sync_interp_hints()
        else:
            self._w_interp_hints.update("")

    def _sync_interp_hints(self) -> None:
        from nekomata.screens.draw import Phase

        if self._dialog.is_streaming:
            pass
        elif self._phase == Phase.DONE and self._first_interp_done:
            self._update_followup_hints()
        elif self._phase == Phase.DONE:
            self._w_interp_hints.update(
                Text(f"I {_STR['hint_interpret']}", style=C_OVERLAY0)
            )

    def _available_boxes(self) -> list[str]:
        from nekomata.screens.draw import Phase

        if self._phase == Phase.PICK:
            return ["deck"]
        if self._phase == Phase.FLIP:
            return ["spread"]
        if self._dialog.fullscreen:
            boxes = []
            if self._detail.visible:
                boxes.append("detail")
            if self._dialog.is_visible:
                boxes.append("interp")
            return boxes or ["interp"]
        boxes = []
        boxes.append("spread")
        if self._detail.visible:
            boxes.append("detail")
        if self._dialog.is_visible:
            boxes.append("interp")
        return boxes

    # -- Footer / phase UI --

    def _update_footer_fullscreen(self) -> None:
        d_hint = _STR["detail_hide"] if self._detail.visible else _STR["detail_show"]
        f_hint = (
            _STR["followup_remaining"].format(remaining=self._followup_remaining)
            if self._first_interp_done and self._followup_remaining > 0
            else ""
        )
        h_hint = (
            _STR["fullscreen_exit" if self._dialog.fullscreen else "fullscreen_enter"]
            if self._dialog.is_visible
            else ""
        )
        i_hint = "" if self._dialog.is_visible else _STR["hint_interpret"]
        parts = [d_hint, h_hint, f_hint, i_hint, _STR["hint_back"]]
        self._w_footer.update(Text("  ".join(p for p in parts if p), style=C_OVERLAY0))

    def _update_phase_ui(self) -> None:
        from nekomata.screens.draw import Phase
        from nekomata.render.styles import C_LAVENDER

        lbl = f"bold {C_LAVENDER}"
        if self._phase == Phase.PICK:
            self._deck_exit_started = False
            self._w_deck_section.styles.opacity = 1.0
            self._w_deck_section.styles.offset = (0, 0)
            if self._pick_index < self._n_positions:
                pos_name = self._spread.positions[self._pick_index].name
                remaining = self._n_positions - self._pick_index
                spread_text = _STR["pick_next"].format(
                    remaining=remaining, name=pos_name
                )
            else:
                spread_text = _STR["pick_done"]
            self._w_spread_label.update(Text(spread_text, style=lbl))
            self._w_deck_label.update(
                Text(
                    _STR["pick_label"].format(
                        picked=self._pick_index, total=self._n_positions
                    ),
                    style=lbl,
                )
            )
            self._w_footer.update(Text(_STR["hint_pick"], style=C_OVERLAY0))
            self._w_deck_section.display = True
        elif self._phase == Phase.FLIP:
            if not self._deck_exit_started:
                self._deck_exit_started = True
                self._animate_deck_exit()
            unrevealed = sum(1 for s in self.query(SpreadSlot) if not s.is_revealed)
            self._w_spread_label.update(
                Text(_STR["flip_label"].format(unrevealed=unrevealed), style=lbl)
            )
            self._w_footer.update(Text(_STR["hint_flip"], style=C_OVERLAY0))
        elif self._phase == Phase.DONE:
            self._w_deck_section.display = False
            self._w_spread_label.update(Text(_STR["done_label"], style=lbl))
            self._update_footer_fullscreen()

    # -- Flip phase --

    async def on_spread_slot_flipped(self, event: SpreadSlot.Flipped) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.FLIP:
            return
        event.stop()
        await event.slot.flip()
        self._update_phase_ui()

        slots = list(self.query(SpreadSlot))
        if all(s.is_revealed for s in slots):
            if self.app.animation_enabled:
                self.run_worker(self._completion_shimmer(slots), exclusive=False)
            self._phase = Phase.DONE
            self._box.active_box = "spread"
            self._box.update_highlights()
            self._detail.show(
                slots[0] if slots else None,
                sync_interp=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(
                    self._w_main_area, self._detail.visible
                ),
            )
            self._update_phase_ui()
            for s in slots:
                s.remove_class("selected")
            slots[0].add_class("selected")
            slots[0].focus()
        else:
            unrevealed = [s for s in slots if not s.is_revealed]
            if unrevealed:
                unrevealed[0].focus()

    async def on_spread_slot_selected(self, event: SpreadSlot.Selected) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.DONE:
            return
        event.stop()
        for s in self.query(SpreadSlot):
            s.remove_class("selected")
        event.slot.add_class("selected")
        self._detail.update(event.slot)

    async def _completion_shimmer(self, slots: list[SpreadSlot]) -> None:
        if not self.app.animation_enabled:
            return
        for i, slot in enumerate(slots):
            self.set_timer(0.01 + i * 0.08, lambda s=slot: self._pulse_slot(s))
        await asyncio.sleep(len(slots) * 0.08 + 0.22)

    @staticmethod
    def _pulse_slot(slot: SpreadSlot) -> None:
        slot.add_class("glow")
        slot.set_timer(0.22, lambda: slot.remove_class("glow"))

    # -- Detail toggle --

    def action_toggle_detail(self) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.DONE:
            return
        if self._detail.visible:
            if self._box.active_box == "detail":
                self._box.active_box = "interp" if self._dialog.fullscreen else "spread"
                self._box.update_highlights()
                self._box.focus_widget()
            center_spread = (
                None if self._dialog.fullscreen else self._center_spread_area
            )
            self._detail.hide(
                sync_interp=self._sync_interp_layout, center_spread=center_spread
            )
        else:
            self._detail.show(
                sync_interp=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(
                    self._w_main_area, self._detail.visible
                ),
            )
            slots = list(self.query(SpreadSlot))
            if slots:
                self._detail.update(slots[0])
                if not self._dialog.fullscreen:
                    slots[0].focus()
            if self._dialog.fullscreen:
                self._box.active_box = "detail"
                self._box.update_highlights()
                self._box.focus_widget()
        self._update_phase_ui()

    # -- Follow-up --

    def key_f(self, event: Key) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.DONE:
            return
        if not self._dialog.is_visible or self._dialog.is_streaming:
            return
        if self._followup_remaining <= 0 and not self._followup_visible:
            return
        event.stop()
        self._toggle_followup()

    def _toggle_followup(self) -> None:
        if self._followup_visible:
            self._hide_followup()
        else:
            self._show_followup()

    def _show_followup(self) -> None:
        self._followup_visible = True
        self._w_followup_input.value = ""
        self._w_followup_section.display = True
        if self.app.animation_enabled:
            self._w_followup_section.styles.opacity = 0
            self._w_followup_section.styles.offset = (0, 1)
        self._w_followup_section.add_class("visible")
        if self.app.animation_enabled:
            self._w_followup_section.styles.animate(
                "opacity", 1.0, duration=0.24, easing=EASE
            )
            self._w_followup_section.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.30,
                easing=EASE_SPRING,
            )
        self._w_followup_input.focus()

    def _hide_followup(self) -> None:
        self._followup_visible = False
        if self.app.animation_enabled:
            self._w_followup_section.styles.animate(
                "opacity", 0.0, duration=0.18, easing=EASE
            )
            self._w_followup_section.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 1)),
                duration=0.24,
                easing=EASE,
            )
            self.set_timer(0.24, self._finish_followup_hide)
        else:
            self._finish_followup_hide()

    def _finish_followup_hide(self) -> None:
        self._w_followup_section.remove_class("visible")
        self._w_followup_section.display = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "followup-input":
            return
        event.stop()
        question = event.value.strip()
        if not question:
            return
        self._hide_followup()
        self._followup_remaining -= 1
        self._start_followup(question)

    def _start_followup(self, question: str) -> None:
        self._followup_question = question
        self._followup_active = True
        self._dialog._streaming = True
        self._stream.streaming = True
        self._stream.reset(append=True)
        self._dialog.fit_height(self._w_main_area, self._detail.visible)
        self.run_worker(
            self._stream.run_followup(
                self._messages_history, question, lambda: self._cancelled
            ),
            exclusive=True,
        )

    def _update_followup_hints(self) -> None:
        if self._dialog.is_streaming or not self._first_interp_done:
            return
        parts = [_STR["done_marker"]]
        if self._followup_remaining > 0:
            parts.append(
                _STR["followup_remaining"].format(remaining=self._followup_remaining)
            )
        parts.append(
            _STR["fullscreen_exit" if self._dialog.fullscreen else "fullscreen_enter"]
        )
        parts.append(_STR["copy_text"])
        parts.append(_STR["export_image"])
        self._w_interp_hints.update(Text("  ".join(parts), style=C_OVERLAY0))

    # -- Fullscreen / Copy / Export --

    def key_h(self, event: Key) -> None:
        from nekomata.screens.draw import Phase

        if self._phase != Phase.DONE or not self._dialog.is_visible:
            return
        event.stop()
        self._dialog.toggle_fullscreen(self._w_main_area)
        self._update_followup_hints()
        self._update_footer_fullscreen()

    def key_c(self, event: Key) -> None:
        from nekomata.screens.draw import Phase

        if (
            self._phase != Phase.DONE
            or not self._first_interp_done
            or self._dialog.is_streaming
        ):
            return
        if not self._dialog.is_visible:
            return
        event.stop()
        if self._initial_interp_content:
            ok = _copy_text_to_clipboard(self._initial_interp_content)
            msg = _STR["copy_success"] if ok else _STR["copy_failed"]
            self._w_interp_hints.update(Text(msg, style=C_MAUVE if ok else C_OVERLAY0))
            self.set_timer(2.0, self._update_followup_hints)

    def key_e(self, event: Key) -> None:
        from nekomata.screens.draw import Phase

        if (
            self._phase != Phase.DONE
            or not self._first_interp_done
            or self._dialog.is_streaming
        ):
            return
        if not self._dialog.is_visible:
            return
        event.stop()
        if self._initial_interp_content:
            self.run_worker(self._export_image(), exclusive=True)

    async def _export_image(self) -> None:
        tmp_path = ""
        try:
            img = render_interp_image(
                self._initial_interp_content,
                self._drawn_cards,
                lang=self.app.config.lang,
                question=self._question,
            )
            tmp_path = _save_tmp_image(img)
            ok = _copy_image_to_clipboard(tmp_path)
        except Exception:
            ok = False
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        msg = _STR["export_success"] if ok else _STR["export_failed"]
        self._w_interp_hints.update(Text(msg, style=C_MAUVE if ok else C_OVERLAY0))
        self.set_timer(2.0, self._update_followup_hints)

    # -- Interpretation / back actions --

    def action_interpret(self) -> None:
        from nekomata.screens.draw import Phase

        if self._phase == Phase.DONE and not self._dialog.is_streaming:
            self._cancelled = False
            self._dialog.show(
                sync_layout=self._sync_interp_layout,
                fit_height=lambda: self._dialog.fit_height(
                    self._w_main_area, self._detail.visible
                ),
            )
            self._sync_interp_hints()
            self._update_footer_fullscreen()
            self._dialog.run(self._drawn_cards, self._question, lambda: self._cancelled)

    def action_handle_back(self) -> None:
        if self._followup_visible:
            self._hide_followup()
            return
        if self._dialog.is_visible:

            def on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self._cancelled = True
                    self._dialog.stop()
                    go_home(self)

            self.app.push_screen(ConfirmExitInterpretation(), callback=on_confirm)
        else:
            go_home(self)
