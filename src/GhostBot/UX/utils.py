from tkinter import ttk
import tkinter as tk


def _format_spot(_spot: str | tuple[int, int]):
    if _spot:
        if isinstance(_spot, str):
            return tuple(_spot.split(" "))
        return f"{' '.join(map(str, _spot))}"
    return ''

type VarConfig = tuple[str, type[str | bool]]

def create_entry(
        widget: tk.Misc,
        label: str,
        row: int,
        column: int,
        var_config: VarConfig = None,
) -> tk.Variable:

    v_name, v_type = var_config
    if v_type is str:  # Entry
        var = tk.StringVar(master=widget, name=v_name, value="")
        ttk.Label(master=widget, text=label, width=15).grid(row=row, column=column)
        tk.Entry(master=widget, textvariable=var, takefocus=False).grid(row=row, column=column + 1)

    elif v_type is bool:  # Checkbutton
        var = tk.BooleanVar(master=widget, name=v_name, value=False)
        ttk.Checkbutton(master=widget, text=label, variable=var, width=13).grid(row=row, column=column)

    else:
        raise TypeError(f"v_type must be str or bool, not {type(v_type)}")

    return var


