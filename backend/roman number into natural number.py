
value={'I':1,"v":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
total1=total2=0
roman=input("enter the roman number=")
for i in range(0,len(roman)):
    if i+1<len(roman) and value[roman[i]]<value[roman[i+1]]:
        total1=total1-value[roman[i]]

    else:
        total2=total2+value[roman[i]]

print(total1+total2)

