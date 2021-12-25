import math
fraction = 0.95
string_len = 15
fraction_string_len = fraction*string_len
one_eighth = "▏"
one_quarter = "▎"
three_eighths = "▍"
one_half = "▌"
five_eighths = "▋"
three_quarters = "▊"
seven_eighths = "▉"
full = "█"

def fraction_to_optimized(fraction):
    fraction = fraction * 15
    num = round(fraction * 8)
    fullbars = math.floor(num/8)
    thing = num - fullbars*8
    if thing == 1:
        last_thing = one_eighth
    elif thing == 2:
        last_thing = one_quarter
    elif thing == 3:
        last_thing = three_eighths
    elif thing == 4:
        last_thing = one_half
    elif thing == 5:
        last_thing = five_eighths
    elif thing == 6:
        last_thing = three_quarters
    elif thing == 7:
        last_thing = seven_eighths
    else:
        last_thing = ""
    string = "`|"+full * fullbars + last_thing + (14-fullbars)*" "+"|`"
    return string
