import sys
import pandas as pd

df= pd.read_csv(sys.argv[1])
df['total']=0
for col in df.columns[1:-1]:
    print('The topper in '+col+' is '+df['Name'].iloc[df[col].idxmax()])
    df['total']+=df[col]
best = 'Best Students in the class are '
for i in df.nlargest(3,'total')['Name']:
    best += i +','
print(best[:-1])


#OUTPUT:

# The topper in Maths is Manasa
# The topper in Biology is Sreeja
# The topper in English is Praneeta
# The topper in Physics is Sagar
# The topper in Chemistry is Manasa
# The topper in Hindi is Aravind
# Best Students in the class are Manodhar,Bhavana,Sourav

#TIME COMPLEXITY
#O(nlog3)