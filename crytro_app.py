import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from openai import OpenAI  # 导入大家伙

# --- 配置区 ---

# 1. 你的 DeepSeek API Key (这里一定要填你自己的！)
# ⚠️ 注意：千万不要把这个 Key 泄露给别人，否则别人会花你的钱/额度
API_KEY = "sk-c5b2d58bf5784ef4b687d845182f1ee7"#AI配置

# 2. 梯子配置 (只用于抓币安数据，DeepSeek 不需要梯子)
#PROXIES = {
    #"http": "http://127.0.0.1:17890",
    #"https": "http://127.0.0.1:17890",
#}
# 这一步去除了，在使用streamlit的云端服务器时，其本身就在美国，也不需要代理网络，后面get访问里面的proxies也需要删除
# 3. 初始化 AI 客户端 (连接到 DeepSeek)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"  # 指向 DeepSeek 的服务器
)

# -------------

st.set_page_config(page_title="AI 币圈分析师", page_icon="📈")
st.title('加密货币情绪分析助手 🪙 (DeepSeek版)')

# 侧边栏
option = st.sidebar.selectbox("选择币种", ['BTC', 'ETH', 'DOGE', 'SOL', 'BNB'])
coin_map = {
    'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'DOGE': 'DOGEUSDT',
    'SOL': 'SOLUSDT', 'BNB': 'BNBUSDT'
}

st.write(f"当前分析目标：**{option}**")

if st.button("🚀 开始 AI 深度分析"):

    # --- 阶段一：获取客观数据 (Binance) ---
    my_bar = st.progress(0)
    status_text = st.empty()  # 占位符，用来动态显示文字

    status_text.info(f"正在从 Binance 获取 {option} 实时行情...")
    time.sleep(0.5)
    my_bar.progress(30)

    current_price = 0
    price_change = "未知"

    try:
        # 1. 抓价格
        symbol = coin_map[option]
        url = "https://api.binance.com/api/v3/ticker/24hr"  # 用这个接口可以顺便拿涨跌幅
        params = {'symbol': symbol}

        # 强制走代理访问币安
        response = requests.get(url, params=params,verify=False,timeout=10)
        data = response.json()

        # 解析数据
        current_price = float(data['lastPrice'])
        price_change_percent = float(data['priceChangePercent'])
        formatted_price = f"${current_price:,.2f}"

        # 颜色逻辑：涨是绿，跌是红
        change_color = "green" if price_change_percent > 0 else "red"
        price_change_str = f"{price_change_percent:+.2f}%"

        my_bar.progress(60)
        status_text.success("行情数据获取成功！正在请求 AI 大脑...")

        # 展示行情看板
        col1, col2 = st.columns(2)
        with col1:
            st.metric("实时价格", formatted_price)
        with col2:
            st.metric("24h 涨跌幅", price_change_str, delta=price_change_str)
            # ... (上面是你原本显示 st.metric 的代码)

        # --- 🆕 新增功能：绘制历史趋势图 ---
        st.write("---")  # 画一条分割线
        st.subheader("📈 过去 30 天价格走势")

        # 1. 获取历史数据 (Binance K-line 接口)
        # interval='1d' 表示每天一根线，limit=30 表示要30天
        history_url = "https://api.binance.com/api/v3/klines"
        history_params = {
            'symbol': coin_map[option],  # 比如 'BTCUSDT'
            'interval': '1d',
            'limit': 30
        }

        # 发送请求 (一定要带上你的梯子 PROXIES !)
        res_history = requests.get(history_url, params=history_params,verify=False,timeout=10)
        history_data = res_history.json()

        # 2. 【数据清洗】把列表转成 Excel 表格 (DataFrame)
        # 币安返回的数据很多列，第0列是时间，第4列是收盘价
        df = pd.DataFrame(history_data)

        # 我们只取前两列，并给它们起个名字
        df = df.iloc[:, :5]  # 只取前5列
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close']  # 重命名列

        # 3. 【类型转换】
        # 时间戳转成人类能看的日期 (2025-12-03)
        df['Date'] = pd.to_datetime(df['Time'], unit='ms')
        # 价格转成数字 (浮点数)
        df['Price'] = df['Close'].astype(float)

        # 4. 【画图】一行代码出图
        # x轴是日期，y轴是价格
        fig = px.line(df, x='Date', y='Price', title=f'{option} 价格走势图')

        # 把线条设成红色或绿色，根据涨跌稍微变一下更好看
        if df['Price'].iloc[-1] > df['Price'].iloc[0]:
            fig.update_traces(line_color='green')#跌绿
        else:
            fig.update_traces(line_color='red')#涨红

        # 5. 上架展示
        st.plotly_chart(fig, use_container_width=True)

        # ... (下面是你原本的 DeepSeek AI 分析代码)
        # ... (前文代码不变)
        df['Date'] = pd.to_datetime(df['Time'], unit='ms')
        df['Price'] = df['Close'].astype(float)

        # --- 🆕 新增：数据科学核心计算 ---
        # 计算 7 日移动平均线 (Rolling Mean)
        df['MA7'] = df['Price'].rolling(7).mean()

        # --- 修改：同时画出两条线 ---
        # y 轴传入一个列表 ['Price', 'MA7']，Plotly 就会自动画两条线
        fig = px.line(df, x='Date', y=['Price', 'MA7'],
                      title=f'{option} 价格 vs MA7 均线走势',
                      color_discrete_map={'Price': 'green', 'MA7': 'orange'})  # 设定颜色

        # 优化图表样式，让它看起来更像金融软件
        fig.update_layout(yaxis_title='美元', xaxis_title='日期')

        st.plotly_chart(fig, use_container_width=True)
        # ... (后文代码不变)

    except Exception as e:
        st.error(f"行情获取失败 (可能是梯子问题): {e}")
        st.stop()  # 如果没有价格，就不让 AI 分析了

    # --- 阶段二：召唤 DeepSeek AI ---
    try:
        # 构造提示词 (Prompt Engineering)
        # 我们把刚才抓到的真实价格喂给 AI，让它基于事实说话
        system_prompt = """
        你是一位拥有10年经验的华尔街加密货币交易员，风格犀利、客观，擅长技术面分析。
        请根据用户提供的币种和当前价格，结合市场心理，写一段简短的分析（100字以内）。
        最后给出一个 0-100 的情绪打分（0是极度恐慌，100是极度贪婪）。
        格式要求：先写分析，最后一行只写分数，格式为 "Score: XX"。
        """

        user_prompt = f"""
        币种：{option}
        当前价格：{formatted_price}
        24小时涨跌幅：{price_change_str}

        请分析现在的市场情绪，并给出操作建议（做多/做空/观望）。
        """

        # 调用 DeepSeek (不走代理，国内直连很快)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )

        # 获取 AI 的回复
        ai_content = response.choices[0].message.content

        my_bar.progress(100)
        status_text.empty()  # 清空提示文字

        # --- 展示结果 ---
        st.write("---")
        st.subheader("🧠 DeepSeek 深度分析报告")

        # 简单处理一下显示（把分数和文字分开会更酷，这里先直接显示全部）
        st.markdown(ai_content)

        st.caption("注：以上分析由 DeepSeek V3 模型实时生成，不构成投资建议。")

    except Exception as e:

        st.error(f"AI 思考超时或出错: {e}")




