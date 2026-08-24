
import argparse

# 创建解析器
parser = argparse.ArgumentParser(description="这是一个示例程序。")

# 添加参数
parser.add_argument("filename", help="处理的文件名")
parser.add_argument("--backup", help="是否创建备份", action="store_true")

# 解析命令行输入
args = parser.parse_args()

# 使用参数
print(f"文件名: {args.filename}")
if args.backup:
    print("将会创建文件备份。")