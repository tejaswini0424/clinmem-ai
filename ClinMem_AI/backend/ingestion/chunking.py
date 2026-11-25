def chunks(text,size=160,overlap=25):
 words=text.split()
 for start in range(0,len(words),size-overlap):
  yield ' '.join(words[start:start+size])
  if start+size>=len(words): break
