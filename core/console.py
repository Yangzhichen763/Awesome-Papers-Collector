

def text_to_foreground_color_code(text):
    if text == "red":
        return 31
    elif text == "green":
        return 32
    elif text == "yellow":
        return 33
    elif text == "blue":
        return 34
    elif text == "purple":
        return 35
    elif text == "cyan":
        return 36
    elif text == "black":
        return 37
    else:
        return 30


# 颜色对应见文章：https://blog.csdn.net/weixin_44478378/article/details/104967241
def colored_print(text, color="green"):
    print(f"\033[0;{text_to_foreground_color_code(color)}m{text}\033[0m")
