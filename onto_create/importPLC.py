import xml.etree.ElementTree as ET
import owlready2 as o2
import os.path

def readXML(filepath):
    mytree = ET.parse(filepath)
    myroot = mytree.getroot()
    return (myroot)

def has_numbers(inputString):
    # check if a string contains number
    return any(char.isdigit() for char in inputString)


def readAttribute(prefix, modelClass):
    str_type = prefix + "type"
    str_id = prefix + "id"
    str_uuid = prefix + "uuid"
    classAttr = ET.Element("")

    classAttr = modelClass.findall('ownedAttribute')
    dic_attr={}

    for attri in classAttr:
        if classAttr != None:
            tag = attri.attrib
            if "Property" in tag[str_type] and not has_numbers(tag['name']):
                className = tag['name']
                dic_attr[className] = {}
                dic_attr[className]["type"] = tag[str_type]
                dic_attr[className]["id"] = tag[str_id]
                dic_attr[className]["uuid"] = tag[str_uuid]
                dic_attr[className]["name"] = className
                for value in attri:
                    if 'lowerValue' in value.tag:
                        dic_attr[className]["min_value"] = value.attrib["value"]
                    elif 'upperValue' in value.tag:
                        dic_attr[className]["max_value"] = value.attrib["value"]
    return dic_attr

def readRelation(prefix, modelClass):
    str_type = prefix + "type"
    str_id = prefix + "id"
    str_uuid = prefix + "uuid"
    classRel = ET.Element("")

    classRel = modelClass.findall('generalization')
    dic_rel={}

    for attri in classRel:
        if classRel != None:
            tag = attri.attrib
            if "Generalization" in tag[str_type] :
                className = "generalization"
                dic_rel[className] = {}
                dic_rel[className]["type"] = tag[str_type]
                dic_rel[className]["id"] = tag[str_id]
                dic_rel[className]["uuid"] = tag[str_uuid]
                dic_rel[className]["general"] = tag["general"]

    return dic_rel

def readClass(filepath):
    FB_dic={}

    modelComment= ET.Element("")
    modelClass = ET.Element("")
    modelDic = {}
    root_data = readXML(filepath)
    prefix = root_data.tag.split("}")[0]+"}"

    str_type = prefix+"type"
    str_id = prefix + "id"
    str_uuid = prefix + "uuid"

    plc_data=ET.parse(filepath)
    #print (root_data.tag,"*",root_data.attrib)

    for x in root_data:
        print(x.tag, x.attrib)
        if  "addData" in x.tag:
            for data in x:
                for ele in data.iter():
                    if "pou" in ele.tag and "pouType" in ele.attrib:
                        if ele.attrib["pouType"]=="functionBlock":
                            if not ele.attrib["name"] in FB_dic.keys():
                                FB_dic[ele.attrib["name"]]=[]
                            for var in ele.iter():
                                if "action" in var.tag and "name" in var.attrib:
                                    print(var.attrib["name"])
                                    FB_dic[ele.attrib["name"]].append(var.attrib["name"])
    return FB_dic

def generateOnto(iri, ontofile,folder_path,sc_number):


    onto = o2.get_ontology(iri)
    with onto:
        class model (onto.information_source):
            comment = ["models in each scnario."]

        class plc(model):
            pass
        class sysml(model):
            pass
        class function_block(plc): pass

        class action(plc): pass

        class has_FB(o2.ObjectProperty): pass

        class has_action(o2.ObjectProperty): pass

        class action_for(o2.ObjectProperty):
            inverse_property = has_action

        class has_info_source (o2.ObjectProperty): pass

        # axioms
        model.is_a.append(has_FB.some(function_block, ))
        function_block.is_a.append(has_action.some(action, ))

        FB_dic={}
        for sc in sc_number:
            filepath = folder_path + sc + "/PLCOpenXML.xml"
            if os.path.isfile(filepath):
                FB_dic=readClass(filepath)
                plant_sc = onto.Scenario("xPPU_Sc" + sc)
                plc_file = plc("xPPU_Sc"+sc+ "_PLCOpenXML")
                plant_sc.has_info_source.append(plc_file)

                for key in FB_dic.keys():
                    fb = function_block("Sc"+sc+"_FB_"+key)
                    plc_file.has_FB.append(fb)
                    if FB_dic[key]:
                        for act in FB_dic[key]:
                            fb_act=action(act)
                            fb.has_action.append(fb_act)
                            fb_act.action_for.append(fb)

        process_info=onto.action.instances()
        #resource_info = onto.Resource.instances()

        for pro in process_info:
            if "." in str(pro):
                process_name= str(pro).split(".")[1]
                new_process = onto["plant_process"](process_name)



    onto.save(file=ontofile)
    # for x in root_data:
    #     if "addData" in x.tag:
    #         modelComment = x.find('pou')
    #         modelClass = x.find('data')
    #     for c in modelClass:
    #         tag = c.attrib
    #         if "Class" in tag[str_type] and not has_numbers(tag['name']):
    #             className = tag['name']
    #             modelDic[className] = {}
    #             modelDic[className]["type"] = tag[str_type]
    #             modelDic[className]["id"] = tag[str_id]
    #             modelDic[className]["uuid"] = tag[str_uuid]
    #             modelDic[className]["name"] = className
    #             modelDic[className]["attribute"] = (readAttribute(prefix, c))
    #             modelDic[className]["relation"] = (readRelation(prefix, c))
    # return modelDic


    # for x in root_data.findall('uml:Model'):
    #     item = x.find('item').text
    #     price = x.find('price').text
    #     print(item, price)

if __name__ == "__main__":
    filepath= "inputs/Sc02/PLCOpenXML.xml"
    readClass(filepath)