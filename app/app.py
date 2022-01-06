import types
from tf.advanced.helpers import NB
from tf.advanced.app import App


MODIFIERS = "lang script intl unc cor rem rec alt vac".strip().split()


def fmt_layoutOrig(app, n, **kwargs):
    return app._wrapHtml(n, "glyph", "")


def fmt_layoutTrans(app, n, **kwargs):
    return app._wrapHtml(n, "glyph", "e")


def fmt_layoutSource(app, n, **kwargs):
    return app._wrapHtml(n, "glyph", "o")


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layoutOrig = types.MethodType(fmt_layoutOrig, app)
        app.fmt_layoutTrans = types.MethodType(fmt_layoutTrans, app)
        app.fmt_layoutSource = types.MethodType(fmt_layoutSource, app)
        super().__init__(*args, **kwargs)

    def _wrapHtml(app, n, ft, kind):
        api = app.api
        F = api.F
        Fs = api.Fs
        after = F.after.v(n) or ""
        isEmpty = F.type.v(n) == "empty"
        material = NB if isEmpty else (Fs(f"{ft}{kind}").v(n) or "")
        clses = " ".join(f"{cf}{Fs(cf).v(n)}" for cf in MODIFIERS if Fs(cf).v(n))
        empty = " empty" if isEmpty else ""
        if clses:
            material = f'<span class="{clses}{empty}">{material}</span>'
        return f"{material}{after}"
