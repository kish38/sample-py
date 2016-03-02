# Script 1

# Developing a calc

num1 = input("Enter number 1:")
num2 = input("Enter number 2:")

ar=['Addition','Difference','Multiplication']
print 'Choose option'
for i in range(len(ar)):
  print i+1,ar[i]

choice= input(':')

print ar[choice-1],num1,", ",num2," : " num1+num2
