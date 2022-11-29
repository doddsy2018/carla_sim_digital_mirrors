start "Main Sim" poetry run python sim_main.py
rem start "Left Mirror" poetry run python left_mirror_view.py
rem start "Right Mirror" poetry run python right_mirror_view.py
start "Mirrors" poetry run python mirror_views.py
rem start "generate_traffic" poetry run python generate_traffic.py