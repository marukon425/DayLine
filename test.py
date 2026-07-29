# num = 128
# x = 0
# while num > 0:
#     x = x + (num %10)
#     num = int(num / 10)
# print(x)

# x = int(input())
# b = "11001"

# i = 1
# while i < 5:
#     if b[i] == "1":
#         x = x + (2**i - 1)
#     i += 1


a = [1, 2, 3, 4, 5]
i = 0
while i < 3:
    a [i+1] = a [i] + a[i+1]

print(a)
