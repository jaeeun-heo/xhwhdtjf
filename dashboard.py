import streamlit as st

st.title("🎉 내 첫 번째 대시보드!")
st.write("Streamlit으로 만든 Python 웹 앱입니다!")

import qrcode

url = "https://너의-배포주소.streamlit.app"  # 실제 배포 주소로 수정!
img = qrcode.make(url)
img.save("qr_code.png")

st.image("qr_code.png", caption="QR 코드를 스캔해보세요!")
