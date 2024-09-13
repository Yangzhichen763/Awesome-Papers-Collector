

def input2array(input_string, split_str=", "):
    """
    将输入的字符串转换为列表
    """
    input_list = input_string.split(split_str)
    return input_list


def array_feed_line(array):
    """

    """
    result = ",\n".join([f"\"{a}\"" for a in array])
    return f"[\n{result}\n]"


# 将输入的字符串转换为列表，并将列表转换为可以直接复制到代码里的列表
if __name__ == "__main__":
    _input_string = input("Enter a string: ")
    _input_list = input2array(_input_string)
    print(array_feed_line(_input_list))
