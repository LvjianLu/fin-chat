以上是我与当前fin-chatbot的对话，还不能够完成工具调用与运行，来回答实时问题。
请重新架构当前的agent flow，使得起可以调用工具来完成这类问题，同时保持原有的chatbot功能，以及多轮对话
1. 保持统一接口的工具调用接口以及执行接口
2. 每个工具调用都有相应的logging info
3. fix the bug

要求:
根据以上需求，完成功能，并修改相应的tests模块，并运用conda env finchat测试以及streamlit run app.py完成代码调试。
如果需要pip install安装，请运用Tsinghua源加速.
将test写入tests中，并保持原来的代码风格
