from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_app_icon(output_path: Path) -> None:
	"""간단한 앱 아이콘(.ico) 생성

	- 파란 배경에 'PDF' 텍스트를 그려 .ico로 저장
	- 윈도우 바로가기 아이콘으로 사용 가능
	"""
	size = 256
	img = Image.new("RGBA", (size, size), (37, 99, 235, 255))  # Tailwind blue-600 계열
	draw = ImageDraw.Draw(img)
	text = "PDF"
	try:
		# 시스템 폰트가 다를 수 있어 기본 폰트로 폴백
		font = ImageFont.truetype("arial.ttf", 120)
	except Exception:
		font = ImageFont.load_default()
	w, h = draw.textbbox((0, 0), text, font=font)[2:]
	x = (size - w) // 2
	y = (size - h) // 2
	draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

	# 여러 해상도를 포함한 ICO로 저장
	ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
	img.save(output_path, format="ICO", sizes=ico_sizes)


def main() -> None:
	out = Path("app_icon.ico")
	create_app_icon(out)
	print(f"WROTE {out.resolve()}")


if __name__ == "__main__":
	main()


