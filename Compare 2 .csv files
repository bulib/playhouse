filein = open('file1.csv') #first input file
#print filein

filein2 = open('file2.csv') #second input file
#print filein2

fileout = open('output.txt', 'w') #output file
#print fileout

a=[]
for t in filein:
    a.append(t.split(','))
  
a2=[]
for t2 in filein2:
    a2.append(t2.split(','))

int = []    
for e in a:
    for e2 in a2:
        if e[0] == e2[4] or e[0] == e2[5] or e[1] == e2[4] or e[1] == e2[5]: #compared keys
            int.append([e[3],e2[0],e2[1]]) #keys added to new array

for z in int:
    fileout.write(z[0] + '\t' + z[1] + '\t' + z[2] +'\n') #new array keys written to output files
    
fileout.close()   
filein2.close()
filein.close()
