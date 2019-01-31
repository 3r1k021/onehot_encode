from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
    
def group_words(list_words):
    total=list_words
    similar_lists=[]
    while len(total)>0:
        word=total[0]
        sim=[]
        to_rem=[]
        sim.append(word)
        to_rem.append(word)
        inner_ind=0
        for word2 in total:
            if inner_ind!=0 and similar(word,word2)>.5:
                #These strings are similar enough
                sim.append(word2)
                to_rem.append(word2)
            #Else: same words, no need to check
            inner_ind+=1
        #Empty lists:
        
        for x in to_rem:
            total.remove(x)
        
        similar_lists.append(sim)
    return similar_lists
#End String Sorting----------------------


orig_order=[]
orig_total=['erik','bobby','erin','maxwell','wellman','erick','bob','ryan','eric','maxwen','brobb','bryan','maximus','henry']
for gr in group_words(['erik','bobby','erin','maxwell','wellman','erick','bob','ryan','eric','maxwen','brobb','bryan']):
    for w in gr[1:]:
        orig_total=[gr[0] if x in gr else x for i,x in enumerate(orig_total)]
print orig_total
 
    
