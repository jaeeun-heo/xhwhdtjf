import streamlit as st

st.title("🎉 내 첫 번째 대시보드!")
st.header("📊 데이터 시각화 프로젝트")
st.subheader("만든 사람: 허재은")
st.markdown("**Streamlit**으로 만든 *깔끔한* 웹 앱입니다!")


import qrcode

url = "https://xhwhdtjf-b7n87zyelbtmnhzzjlp6kq.streamlit.app/"
img = qrcode.make(url)
img.save("qr_code.png")
print("✅ QR 코드가 'qr_code.png'로 저장되었습니다!")
