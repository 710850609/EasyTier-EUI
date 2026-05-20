# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import io
import qrcode

def create_str(qrcode_data:str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        # box_size=10,
        # border=4,  # 规范要求最小 4，不能省
    )
    qr.add_data(qrcode_data)
    qr.make(fit=True)

    buf = io.StringIO()
    qr.print_ascii(out=buf, tty=False)  # tty=False 用普通空格和 █
    return buf.getvalue()

if __name__ == '__main__':
    data = "http://localhost:5666"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,  # 必须 4，否则扫不出
    )
    qr.add_data(data)
    qr.make(fit=True)

    modules = qr.modules
    lines = []

    for row in modules:
        # 每个模块横向 2 个字符
        line = ''.join('██' if cell else '  ' for cell in row)
        # 每个模块纵向 2 行，复制一遍
        lines.append(line)
        # lines.append(line)

    print('\n')
    print( '\n'.join(lines))
