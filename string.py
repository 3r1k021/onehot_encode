    
def check_similar_all(col,ratio):
    outer=0
    inner=0
    sorted_data=set({})
    
    for word in col:
        matches=[]
        deletes=[]
        matches.append(word)
        for i in range(len(col)):
            if i!=outer:
                if similar(col[i],word)>ratio:
                    deletes.append(i)
                    deletes.append(outer)
                    matches.append(col[i])
            inner+=1
        outer+=1
        sorted_data.add(tuple(matches))
        new_col=[]
        for c in col:
            if c in deletes:
                x=-1
                #DO not add
            else:
                new_col.append(c)
        col=new_col
    listA=[]
    for i in sorted_data:
        listA.append(list(set(i)))
    real_list=[]

    for a in listA:
        real_list.append(a.sort())
    return ( OrderedDict((tuple(x), x) for x in listA).values() )    


print (check_similar_all(col,.1))
