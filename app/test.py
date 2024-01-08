

func ='''
def lowercase(message : str) -> str:
    return message.lower()

'''
exec(func)
# print(lowercase("Sai Vishal"))
ans = eval("lowercase('Sai Vishal')")

print(ans)