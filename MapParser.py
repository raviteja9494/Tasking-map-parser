import re


class File:
def __init__(self, name: str, archiveName: str = None, extractSymbol: str = None):
self.name = name
self.archiveName = archiveName
self.extractSymbol = extractSymbol
def dictonary(self):
return {"FileName": self.name,"archiveName": self.archiveName,"extractSymbol":self.extractSymbol}

class LocateRecord:
def __init__(self, chip: str, group: str, section: str, size: int, spaceAddr: int, chipAddr: int, alignment: int):
self.chip = chip
self.group = group
self.section = section
self.size = size
self.spaceAddr = spaceAddr
self.chipAddr = chipAddr
self.alignment = alignment
def dictonary(self):
return {"chip": self.chip,
"group": self.group,
"section": self.section,
"size": self.size,
"spaceAddr": self.spaceAddr,
"chipAddr": self.chipAddr,
"alignment": self.alignment
}

class MapParser():
filename = ""
FileSectionKeywords = {
"UsedResources": re.compile(r'^[\*]+\s*Used Resources\s*[\*]+$'),
"ProcessedFiles": re.compile(r'^[\*]+\s*Processed Files\s*[\*]+$'),
"LinkResult": re.compile(r'^[\*]+\s*Link Result\s*[\*]+$'),
"LocateResults": re.compile(r'^[\*]+\s*Locate Result\s*[\*]+$'),
"UnknownPart": re.compile(r'^[\*]* .* [\*]*$')
}
linesCount = 0
previous = None
ResourceSection = None
LocateResultSection = None

linkerMap = {
"usedResources" : {"memory_usage": [],"space_usage": [],"est_stack_usage": []},
"processedFiles" : [],
"linkResult" : [],
"linkResult_processed" : [],
"locateResult" : {"Sections":[],"Symbols":[]}
}

def __init__(self,filename):
self.filename = filename
self.__parse_Mapfile(self.filename)
return


def __handleUsedResources(self,line: str):

UsedResourceSectionKeywords = {
"MemoryUsage":"* Memory usage in bytes\n",
"SapceUsage":"* Space usage in bytes\n",
}

if line.startswith('*'):
for key, value in UsedResourceSectionKeywords.items():
if line == value:
self.ResourceSection = key
self.previous = None
break

if(self.ResourceSection == "MemoryUsage"):
self.__handle_memory_usage(line)
elif(self.ResourceSection == "SapceUsage"):
self.__handle_space_usage(line)

def __handle_memory_usage(self,line: str):           
regex = re.compile(r'^\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|$')
found = re.match(regex, line)
if found and found[1].strip() != 'Memory':
record = {
"name": found[1].strip(),
"code": int(found[2].strip(), 16),
"data": int(found[3].strip(), 16),
"reserved": int(found[4].strip(), 16),
"free": int(found[5].strip(), 16),
"total": int(found[6].strip(), 16)
}
self.linkerMap["usedResources"]["memory_usage"].append(record)

def __handle_space_usage(self,line: str):           
regex = re.compile(r'^\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|$')
found = re.match(regex, line)
if found and found[1].strip() != 'Space':
record = {
"Space": found[1].strip(),
"NativeUsedRom": 0 if found[2].strip() == '-' else int(found[2].strip(), 16),
"NativeUsedRam": 0 if found[3].strip() == '-' else int(found[3].strip(), 16),
"NativeUsedNVRam": 0 if found[4].strip() == '-' else int(found[4].strip(), 16),
"ForeignUsed ": 0 if found[5].strip() == '-' else int(found[5].strip(), 16),
"Reserved": 0 if found[6].strip() == '-' else int(found[6].strip(), 16),
"FreeRom": 0 if found[7].strip() == '-' else int(found[7].strip(), 16),
"FreeRam": 0 if found[8].strip() == '-' else int(found[8].strip(), 16),
"FreeNVRam": 0 if found[9].strip() == '-' else int(found[9].strip(), 16),
"Total": 0 if found[10].strip() == '-' else int(found[10].strip(), 16),
}
self.linkerMap["usedResources"]["space_usage"].append(record)

def __handleProcessedFiles(self,line: str):

found = re.match(r'^\|\s+(\S.*\S|)\s+\|\s+(\S.*\S|)\s+\|\s+(\S.*\S|)\s+\|$', line)
if found and found[1] != 'File':
file = File(found[1].strip())
# if len(found) > 2:
file.archiveName = found[2].strip()
file.extractSymbol = found[3].strip()
if found[1].strip() == '':
previousFile = self.previous
if previousFile.archiveName and file.archiveName:
previousFile.archiveName += file.archiveName
if previousFile.extractSymbol and file.extractSymbol:
previousFile.extractSymbol += file.extractSymbol
else:
self.previous = file
self.linkerMap["processedFiles"].append(file.dictonary())

def __handleLinkResult(self,line: str):
tableEntryDelimeterRegEx = re.compile(r'^\|-+\|$')
if tableEntryDelimeterRegEx.match(line):
self.previous = None
recordRegEx = re.compile(r'^\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|$')
found = re.match(recordRegEx, line)
if found and found[1].strip() != '[in] File':
if self.previous and found[3].strip() == '' and found[4].strip() == '' and found[6].strip() == '':
previousRecord = self.previous
filename = found[1].strip()
inSection = found[2].strip()
outSection = found[5].strip()
previousRecord["filename"] += filename
previousRecord["inSection"] += ' ' + inSection if inSection.startswith('(') else inSection
previousRecord["outSection"] += ' ' + outSection if outSection.startswith('(') else outSection
else:
record = {"filename": found[1].strip(),
"inSection":found[2].strip(),
"inSize":0 if found[3].strip() == '' else int(found[3].strip(), 16),
"outOffset":0 if found[4].strip() == '' else int(found[4].strip(), 16),
"outSection":found[5].strip(),
"outSize":0 if found[6].strip() == '' else int(found[6].strip(), 16)
}
self.linkerMap["linkResult"].append(record)
self.previous = record

def __process_LinkResult(self):
linkResult = {}

for linkrecord in self.linkerMap["linkResult"]:
filename = linkrecord["filename"]
if filename not in linkResult:
linkResult[filename] = {"FileName": filename,"Bss":0,"Data":0,"Text":0}

if(linkrecord["inSection"].startswith('.bss')):linkResult[filename]["Bss"] += linkrecord["inSize"]
if(linkrecord["inSection"].startswith('.data')):linkResult[filename]["Data"] += linkrecord["inSize"]
if(linkrecord["inSection"].startswith('.text')):linkResult[filename]["Text"] += linkrecord["inSize"]

for value in linkResult.values():
value["Ram"] = value["Bss"] + value["Data"]
value["Rom"] = value["Text"]
self.linkerMap["linkResult_processed"].append(value)

def __handleLocateResult(self,line: str):

LocateResultSectionKeywords = {
"Sections":"* Sections\n",
"Symbols":"* Symbols (sorted on name)\n",
"Symbols_a":"* Symbols (sorted on address)\n"
}

if line.startswith('*'):
for key, value in LocateResultSectionKeywords.items():
if line == value:
self.LocateResultSection = key
self.previous = None
break

if(self.LocateResultSection == "Sections"):
self.__handleLocateResultSections(line)
elif(self.LocateResultSection == "Symbols"):
self.__handleLocateResultSymbols(line)

def __handleLocateResultSections(self,line: str):
tableEntryDelimeterRegEx = re.compile(r'^\|-+\|$')
if tableEntryDelimeterRegEx.match(line):
self.previous = None
recordRegEx = re.compile(r'^\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|$')
found = re.match(recordRegEx, line)
if found and found[1].strip() != 'Chip':
if self.previous and found[1].strip() == '':
previousRecord = self.previous
section = found[3].strip()
previousRecord.section += ' ' + section if section.startswith('(') else section
else:
record = LocateRecord(found[1].strip(), found[2].strip(), found[3].strip(), int(found[4].strip(), 16), int(found[5].strip(), 16), int(found[6].strip(), 16), int(found[7].strip(), 16))
self.linkerMap["locateResult"]["Sections"].append(record.dictonary())
self.previous = record

def __handleLocateResultSymbols(self,line: str):
regex = re.compile(r'^\|([^|]*)\|([^|]*)\|([^|]*)\|$')
found = re.match(regex, line)
if found and found[1].strip() != 'Name':
if found[2].strip() == '':
self.linkerMap["locateResult"]["Symbols"][-1]["Name"] += found[1].strip()
else:
record = {
"Name": found[1].strip(),
"SpaceAddr": int(found[2].strip(), 16),
"Space": found[3].strip()
}
self.linkerMap["locateResult"]["Symbols"].append(record)

def __parse_Mapfile(self,filename):
filesection = ""
with open(filename, 'r') as file:
for line in file:
self.linesCount += 1
if line.startswith('*'):
for key, value in self.FileSectionKeywords.items():
if value.match(line):
filesection = key
self.previous = None
break
if filesection == "UsedResources":
self.__handleUsedResources(line)
elif filesection == "ProcessedFiles":
self.__handleProcessedFiles(line)
elif filesection == "LinkResult":
self.__handleLinkResult(line)
elif filesection == "LocateResults":
self.__handleLocateResult(line)

self.__process_LinkResult()

return

def get_used_resources(self):
return self.linkerMap["usedResources"]
def get_processed_files(self):
return self.linkerMap["processedFiles"]
def get_link_result(self):
return self.linkerMap["linkResult"]
def get_link_result_processed(self):
return self.linkerMap["linkResult_processed"]
def get_locate_result(self):
return self.linkerMap["locateResult"]

def get_linkermap(self):
return self.linkerMap


# pa = MapParser("P0304_HMIG.map")
