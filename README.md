# Heat Conduction Simulator

A Python / PySide6 interactive simulation of thermal conduction between two physical bodies.

## Project Structure
- `Body.py` – Physical `Body` class with mass, specific heat capacity, temperature, and `add_heat(delta_q)` method.
- `Main.py` – Main GUI (`HeatTransfer`), real-time thermal color visualization, simulation timer, material presets, optional heaters, and equilibrium auto-stop.
- `GraphWindow.py` – Embedded Matplotlib plotting window (`Draw`, `Clear`, `Export to CSV` with automatic spreadsheet launch).
- `AboutWindow.py` – Project info, diagram, and clickable GitHub link.
- `style.css` – Shared QSS stylesheet used across all windows.

## Requirements
```bash
pip install PySide6 matplotlib
```

## Running
```bash
python3 Body.py   # Run Stage 1 unit check
python3 Main.py   # Launch the full simulator
```
