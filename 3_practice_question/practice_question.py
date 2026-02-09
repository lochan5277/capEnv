x=int(input("Enter a number linked list: "))
a=list(map(int,input("Enter the linked list of numbers: ").split()))[:x]

if x % 2 == 0:
    mid = x // 2
else:
    mid=(x+1)//2
    
a.pop(mid-1)
print(a)