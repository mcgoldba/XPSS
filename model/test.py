import subprocess, tempfile

out = tempfile.mkstemp(suffix='.out')
err = tempfile.mkstemp(suffix='.err')
input = tempfile.mkstemp(suffix='.input')

p = subprocess.Popen(
    ['C:/Users/deluca/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/qepanet/bin/64bit/WindowsPE/epanet2d.exe',
     u'D:/Temp/րKalibreerimata mudel (jaan2019) – lõplik/Acquedotto Levico Terme.inp',
     u'D:/Temp/րKalibreerimata mudel (jaan2019) – lõplik/Acquedotto Levico Terme.rpt',
     u'D:/Temp/րKalibreerimata mudel (jaan2019) – lõplik/Acquedotto Levico Terme.out'],
    cwd=tempfile.gettempdir(),
    stdin=input[0],
    stdout=subprocess.PIPE,
    stderr=err[0])

while True:
    for byte_line in iter(p.stdout.readline, ''):
        line = byte_line.decode('utf8', errors='backslashreplace').replace('\r', '')
        print(line)
        if not line:
            break
