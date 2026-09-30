# 하지혜님 
import os

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


# .env 파일 읽기
load_dotenv()


def make_html_email(recommended_numbers, stores):
    """
    추천 번호와 명당 Top 3를
    HTML 이메일 형태로 만든다.
    """

    # --------------------------------
    # 추천 번호 HTML 만들기
    # --------------------------------

    balls = ""

    for number in recommended_numbers:

        balls += f"""
        <span style="
            display:inline-flex;
            width:50px;
            height:50px;
            border-radius:50%;
            background:#f2c94c;
            align-items:center;
            justify-content:center;
            margin:5px;
            font-size:18px;
            font-weight:bold;
            color:#222;
        ">

            {number}

        </span>
        """


    # --------------------------------
    # 명당 HTML 만들기
    # --------------------------------

    store_html = ""


    for index, store in enumerate(
        stores[:3],
        start=1
    ):

        store_name = store.get(
            "store_name",
            "매장명 없음"
        )

        region = store.get(
            "region",
            ""
        )

        win_count = store.get(
            "win_count",
            0
        )

        search_url = store.get(
            "search_url",
            "#"
        )


        store_html += f"""

        <div style="
            border:1px solid #ddd;
            border-radius:10px;
            padding:15px;
            margin:10px 0;
        ">

            <h3>
                {index}위.
                {store_name}
            </h3>

            <p>
                지역:
                {region}
            </p>

            <p>
                <strong>
                    1등 배출:
                    {win_count}회
                </strong>
            </p>

            <a
                href="{search_url}"
                target="_blank"
            >

                카카오맵에서 매장 찾기

            </a>

        </div>

        """


    # --------------------------------
    # 전체 HTML 이메일
    # --------------------------------

    html = f"""

    <!DOCTYPE html>

    <html lang="ko">

    <head>

        <meta charset="UTF-8">

        <title>
            로또 뉴스레터
        </title>

    </head>


    <body style="
        font-family:Arial, sans-serif;
        background:#f5f5f5;
        padding:30px;
    ">


        <div style="
            max-width:650px;
            margin:0 auto;
            background:white;
            padding:30px;
            border-radius:15px;
        ">


            <h1>
                🎰  Lucky Lotto
            </h1>


            <p>
                이번 주 통계 기반 추천 번호입니다.
            </p>


            <hr>


            <h2>
                🎯 추천 번호
            </h2>


            <div>

                {balls}

            </div>


            <hr>


            <h2>
                📍 1등 명당 Top 3
            </h2>


            {store_html}


            <p style="
                color:#777;
                margin-top:30px;
            ">

                본 메일은
                로또 프로젝트
                시연용 뉴스레터입니다.

            </p>


        </div>


    </body>

    </html>

    """


    return html



def send_lotto_email(
    to_email,
    recommended_numbers,
    stores
):
    """
    Gmail SMTP를 이용해
    HTML 이메일을 발송한다.
    """

    # --------------------------------
    # .env에서 Gmail 정보 가져오기
    # --------------------------------

    sender_email = os.getenv(
        "EMAIL_ADDRESS"
    )

    sender_password = os.getenv(
        "EMAIL_PASSWORD"
    )


    # --------------------------------
    # 이메일 정보가 없는 경우
    # --------------------------------

    if not sender_email:

        raise ValueError(
            "EMAIL_ADDRESS가 없습니다."
        )


    if not sender_password:

        raise ValueError(
            "EMAIL_PASSWORD가 없습니다."
        )


    # --------------------------------
    # HTML 이메일 생성
    # --------------------------------

    html_content = make_html_email(
        recommended_numbers,
        stores
    )


    # --------------------------------
    # 이메일 객체 생성
    # --------------------------------

    message = MIMEMultipart(
        "alternative"
    )


    message["Subject"] = (
        "🎰 lucky lotto - 이번 주 로또 추천 뉴스레터"
    )

    message["From"] = sender_email

    message["To"] = to_email


    # HTML 내용 첨부

    message.attach(
        MIMEText(
            html_content,
            "html",
            "utf-8"
        )
    )


    # --------------------------------
    # Gmail SMTP 서버 연결
    # --------------------------------

    with smtplib.SMTP(
        "smtp.gmail.com",
        587
    ) as server:


        # TLS 암호화

        server.starttls()


        # Gmail 로그인

        server.login(
            sender_email,
            sender_password
        )


        # 메일 발송

        server.sendmail(
            sender_email,
            to_email,
            message.as_string()
        )


    return True
