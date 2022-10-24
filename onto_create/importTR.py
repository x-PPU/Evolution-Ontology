import pandas as pd
import re
import csv
#from owlready2 import *
import owlready2 as o2
import os.path

def readCSV(filepath):
    df = pd.read_excel(filepath,header = None)
    data_list = df.values.tolist()
    print(data_list)

def replace_spec_char(list):
    for i in range(len(list)-1):
        list[i] = list[i].replace(' ', '')
        list[i] = list[i].replace('(', '_')
        list[i] = list[i].replace(')', '')
        list[i] = list[i].replace('ä', 'ae')
        list[i] = list[i].replace('Ä', 'Ae')
        list[i] = list[i].replace('ö', 'oe')
        list[i] = list[i].replace('Ö', 'Oe')
        list[i] = list[i].replace('ü', 'ue')
        list[i] = list[i].replace('Ü', 'Ue')
        list[i] = list[i].replace('ß', 'ss')
        list[i] = list[i].replace('fuer', '_')

    return list

def is_empty( list):
    """ This function checks if given string is empty
     or contain only shite spaces"""
    result=True
    for i in list:
        if i!='':
            return False
    return result

def has_numbers(inputString):
# check if a string contains number
    return any(char.isdigit() for char in inputString)

def get_unit(string)->list:

    if " " in string:
        result=string.split(" ")
        if result[0]=="":
            result=result[1:]
    result[0]= convert_to_digital(result[0])
    return result

def convert_to_digital(string):
    if not '.' in string:
        return int(string)
    else:
        return float(string)


# function to check if  a string is NaN
def readFile(iri, ontofile, folder_path, sc_number):
    onto = o2.get_ontology(iri)

    with onto:
        # classes
        class Scenario(o2.Thing):
            comment = ["source file of the resource"]
        class information_source(o2.Thing):
            information_source = ["Information sources in each secnario."]
        # class Model(Scenario):
        #     parameter = ["Models in data sources."]
        class document(information_source):
            parameter = ["document in each scnario."]
        class document_info(document):
            parameter = ["Information of the document"]

        class model(information_source):pass

        class version(document_info): pass


        # class file_name(Document_info):pass

        class plant_info(document):
            parameter = ["Plant information in document."]

        class research_plant(o2.Thing): pass

        class plant_resource(research_plant): pass

        class plant_product(research_plant): pass

        class plant_process(research_plant): pass

        class logistics_process(plant_process):
            pass

        class manufacturing_process(plant_process):
            pass

        class assembly_process(plant_process):
            pass

        class plant_operation(research_plant):
            pass

        class plant_task(research_plant):
            pass

        class plant_station(research_plant):
            pass

        class plant_component(research_plant):
            pass
        class sensor(plant_resource):
            pass

        class actuator(plant_resource):
            pass



        #model data
        #class model(o2.Thing):pass

        # object properties
        class has_info(o2.ObjectProperty): pass

        class has_version(o2.ObjectProperty):pass

        class has_variable(o2.ObjectProperty):
            pass

        class info_for(o2.ObjectProperty):
            inverse_property = has_info

        class has_info_source(o2.ObjectProperty):pass

        class defined_in(o2.ObjectProperty, o2.TransitiveProperty):
            pass

        class has_station(o2.ObjectProperty):
            pass

        class has_component(o2.ObjectProperty):
            pass

        class performs_task(o2.ObjectProperty):
            pass

        class includes_task(o2.ObjectProperty):
            pass

        class performs_operation(o2.ObjectProperty):
            pass

        class requires_component(o2.ObjectProperty):
            pass
        # data properties
        class has_max_value(o2.DatatypeProperty):pass

        class has_min_value(o2.DatatypeProperty):pass

        # axioms
        Scenario.is_a.append(has_info_source.some(document, ))
        Scenario.is_a.append(has_info_source.some(model, ))
        sensor.is_a.append(defined_in.some(document, ))
        actuator.is_a.append(defined_in.some(document, ))
        plant_resource.is_a.append(has_station.some(plant_station, ))
        plant_station.is_a.append(has_component.some(plant_component, ))
        plant_station.is_a.append(performs_operation.some(plant_operation, ))
        plant_component.is_a.append(performs_task.some(plant_task, ))
        plant_process.is_a.append(includes_task.some(plant_task, ))
        plant_product.is_a.append(requires_component.some(plant_component, ))




        for sc in sc_number:

            path = folder_path + sc + "/component_list.csv"

            plant_sc=Scenario("xPPU_Sc"+sc)


            if os.path.isfile(path):
                report = document("xPPU_Sc" + sc + "_technical_report")
                report_version = version("TUM-AIS-TR-01-14-02")
                report.has_version.append(report_version)

                plant_sc.has_info_source.append(report)
                with open(path,encoding="UTF-8") as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=';')

                    headers = next(csv_reader)
                    row_length= len(headers)


                    for i in range(0, len(headers)):
                        info = o2.types.new_class(headers[i], (plant_info,))

                    for row in csv_reader:
                        row = replace_spec_char(row)
                        if is_empty(row):
                            continue
                        else:
                            for j in range(0, row_length):
                                info = o2.types.new_class(headers[j], (plant_info,))
                                reso = onto.Resource(row[1])
                                report.has_info.append(reso)
                                if j != 1:
                                    if row[j]!="":
                                        instance = info(row[j])
                                        reso.has_info.append(instance)
                                        instance.info_for.append(reso)

        description_info=onto.Description.instances()
        #resource_info = onto.Resource.instances()

        for re in description_info:
            if "_" in str(re):
                re_name=str(re).split("_")[1]
                if "Switch" in re_name:
                    pl_re = o2.types.new_class(re_name, (sensor,))
                elif "Valve" in re_name or "Motor" in re_name:
                    pl_re = o2.types.new_class(re_name, (actuator,))
                #pl_re(re.info_for[0])



    onto.save(file=ontofile)


if __name__ == "__main__":
    onto_file= "outputs/files.owl"
    tax_file = "inputs/Sc00/component_list.csv"
    output_file = "outputs/Files/Files.owl"
    iri = "http://example.org/onto-example.owl"
    readFile(iri, onto_file, tax_file)