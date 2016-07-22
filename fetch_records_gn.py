from owslib.iso import namespaces
from owslib.csw import CatalogueServiceWeb
from owslib import fes
from lxml import etree
import os.path


def safe_xpath(xml_root, path, namespaces=None, use_iter=False):
    '''
    Returns an element of an XPath query as either a single element if the
    query only returns a single element, a list if it returns multiple elements
    or None if no elements are returned.

    :param xml_root: Root etree object
    :param str path: XPath
    :param dict namespaces: XML Namespace Mapping, defaults to xml_root.nsmap
    :param bool use_iter: Returns a list, no matter what
    '''
    r = xml_root.xpath(path, namespaces=namespaces or xml_root.nsmap)
    if use_iter:
        return r
    elif len(r) == 1:
        return r[0]
    elif r:
        return r
    else:
        return None


class ISOPaths(object):
    '''
    Class that holds attributes of all fields and XPaths that resolve to that field in a document
    '''
    identifier = "./gmd:fileIdentifier/gco:CharacterString/text()[1]"
    title = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()[1]"
    abstract = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString/text()[1]"
    thesaurus_name = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString/text()"

    # A lot of gmd:MD_DataIdentification here.  Consider traversing from this element
    # Temporal Extents
    start_time = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text()"
    end_time = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition/text()"

    geo_extents = "./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:%s/gco:Decimal/text()[1]"

    # Geospatial Bounding Box

    west_longitude = geo_extents % "westBoundLongitude"
    south_latitude = geo_extents % "southBoundLatitude"
    east_longitude = geo_extents % "eastBoundLongitude"
    north_latitude = geo_extents % "northBoundLatitude"

    # GLOS Specific
    glos_categories = './gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString="GLOS Categories"]/gmd:keyword/gco:CharacterString/text()'

    # keywords
    kw_xpath = './gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString!="GLOS Categories"]/gmd:keyword/gco:CharacterString/text()'

    # BWA: there are many different ways the online resources can be represented
    online_resources = "./gmd:distributionInfo/gmd:MD_Distribution//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource"

    thumbnail = '/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic[gmd:fileDescription/gco:CharacterString="thumbnail"]/gmd:fileName/gco:CharacterString/text()'

    # parameters
    parameters = './gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords[gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString="Variables"]/gmd:keyword/gco:CharacterString/text()'

    # protocols
    geojson_url = './gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gco:CharacterString="GeoJSON"]/gmd:linkage/gmd:URL/text()'

    service_wms_url = "./gmd:identificationInfo/srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata[srv:operationName/gco:CharacterString='GetCapabilities']/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()"
    online_resource_wms = "./gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gco:CharacterString='OGC:WMS-1.3.0-http-get-capabilities']/gmd:linkage/gmd:URL/text()"

    info_url = './gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:name/gco:CharacterString="Info URL"]/gmd:linkage/gmd:URL/text()'
    links = './gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gco:CharacterString="WWW:LINK-1.0-http--link"]'
    pdfs = './gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gco:CharacterString="application/pdf"]'

def fetch_records(csw_endpoint, filt_q=None, write_dir=None):
    """
    Takes an optional fes filter and write directory.  If write_dir
    is set, write ISOs to that directory.
    """
    csw_endpoint.getrecords2(outputschema=namespaces['gmd'], constraints=filt_q,
                            esn='full', maxrecords=1000)

    myglos_records = []
    for identifier, record in csw_endpoint.records.iteritems():
        xml_root = etree.fromstring(record.xml)
        dictionaries = safe_xpath(xml_root, ISOPaths.thesaurus_name)

        if dictionaries and 'GLOS Categories' in dictionaries:
            myglos_records.append(xml_root)
        if write_dir:
            ident = record.identifier.split('/')[-1]
            fname = os.path.join('{}'.format(write_dir),
                                    '{}.xml'.format(ident))
            xml_root.getroottree().write(fname)
            print("Wrote", fname)

    return myglos_records

def main():
    '''By default, look for tds endpoints and then store the ISOs in a waf'''
    csw = CatalogueServiceWeb('http://data.glos.us/metadata/srv/eng/csw')
    # list of FES filter specs
    filt = [fes.PropertyIsLike('csw:AnyText', '%tds.glos.us%')]
    folder = '/tmp/glos_waf'
    fetch_records(csw, filt, folder)

if __name__ == '__main__':
    main()
