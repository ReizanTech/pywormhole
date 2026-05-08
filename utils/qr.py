import qrcode
from io import BytesIO
from PIL import Image, ImageTk


def generate_qr_image(
    data: str,
    box_size: int = 6,
    border: int = 2,
) -> ImageTk.PhotoImage:
    """
    توليد صورة QR Code من نص

    Args:
        data     : النص (كود الجلسة)
        box_size : حجم كل خلية
        border   : حجم الحاشية

    Returns:
        ImageTk.PhotoImage جاهزة لـ Tkinter
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img: Image.Image = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGB")

    return ImageTk.PhotoImage(img)


def generate_qr_bytes(data: str) -> bytes:
    """
    توليد QR Code كـ PNG bytes
    للحفظ أو النسخ

    Returns:
        bytes : صورة PNG
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()