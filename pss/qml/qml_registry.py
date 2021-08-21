from XPSS.utils import get_root_dir
import pathlib

QML_FILEPATH = pathlib.Path(__file__).parent.resolve()

qml_files = {
    "System Geometry": {
        'Pipes': 'pipes_dia_labels.qml',
        'Junctions': 'junctions_node_labels.qml'
        },
    "Results": {
        'Pipes': 'pipes_vel_labels.qml',
        'Junctions': 'junctions_pres_labels.qml'
        }
    }
