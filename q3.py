original = "I love driving. drivingAAA is awesome. I love driving my car. I know a lot about driving."

target = "driving"
replacement = "racing"

x = original.replace(".", " .")

tar = " " + target + " "
rep = " " + replacement + " "

y = x.replace(tar, rep , 3)
z = y.replace(rep, tar, 2)

out = z.replace(" .", ".")
print(out)



print(original)
print(x)
print(y)
print(z)
print(out)
