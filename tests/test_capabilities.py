import copy
import json
import tempfile
import unittest
from pathlib import Path
from signallab_pc.hp_inventory import extract_menus,source_inventory
from signallab_pc.capabilities import build_catalog,validate_catalog,compare_catalogs,check_reference,capability_id,save_catalog,load_catalog
from signallab_pc.navigation import MENUS

SAMPLE='''Example()
BEGIN
  // SSMenu("fake",{"fake"},1);
  op:=SSMenu("Visible",{"comma, brace }", "Apply: "+STRING(N)+" samples", "Cancel"},1);
  op:=SSMenu(title,items,1);
END;
'''
class InventoryTests(unittest.TestCase):
    def test_nested_expressions_are_single_options(self):
        menus=extract_menus(SAMPLE);self.assertEqual(len(menus),2)
        m=menus[0];self.assertEqual(m['caller'],'Example');self.assertEqual(len(m['options']),3)
        self.assertEqual(m['options'][0]['label'],'comma, brace }');self.assertTrue(m['options'][1]['dynamic']);self.assertIsNone(m['options'][1]['label'])
        self.assertIn('STRING(N)',m['options'][1]['expression']);self.assertTrue(menus[1]['dynamic_options'])
    def test_definition_and_quoted_calls_are_not_calls(self):
        code='SSMenu(a,b,c)\nBEGIN\n x:="SSMenu(fake)";\n END;\n/* SSMenu("ignored",{},1); */\n'+SAMPLE
        self.assertEqual(len(extract_menus(code)),2)
    def test_commented_function_does_not_change_caller(self):
        code='Real()\nBEGIN\n/* Fake()\nBEGIN */\nSSMenu("Visible",{"A"},1);\nEND;'
        self.assertEqual(extract_menus(code)[0]['caller'],'Real')
    def test_stable_ids_after_comment_and_line_insertion(self):
        old=extract_menus(SAMPLE);new=extract_menus('// comment\n\n'+SAMPLE)
        self.assertEqual([x['id'] for x in old],[x['id'] for x in new]);self.assertEqual(new[0]['line'],old[0]['line']+2)
    def test_repeated_titles_are_distinct(self):
        menus=extract_menus('F()\nBEGIN\nSSMenu("A",{"x"},1);SSMenu("A",{"y"},1);\nEND;')
        self.assertNotEqual(menus[0]['id'],menus[1]['id'])
    def test_unclosed_and_mismatched_calls_rejected(self):
        for code in ['SSMenu("x",{"a"},1','SSMenu("x",{"a"],1)','SSMenu("unterminated)','/* unterminated SSMenu("x",{},1)']:
            with self.assertRaises(ValueError):extract_menus(code)
    def test_authoritative_source_dynamic_snr_and_all_calls(self):
        path=Path(__file__).resolve().parents[1]/'references/SignalLab_App_5.0.hppl'
        result=source_inventory(path.read_bytes());self.assertEqual(result['counts']['menu_calls'],157)
        menu=next(m for m in result['menus'] if m['title']=='Aplicar intervalo SNR')
        self.assertEqual(len(menu['options']),2);self.assertTrue(menu['options'][0]['dynamic'])
        self.assertEqual(result['counts']['dynamic_option_lists'],5)

class CapabilityTests(unittest.TestCase):
    def setUp(self):self.catalog=build_catalog(SAMPLE.encode())
    def test_every_route_has_unique_id_and_no_parity_claim(self):
        expected=[capability_id(item) for items in MENUS.values() for item in items]
        actual=[entry['id'] for entry in self.catalog['capabilities']]
        self.assertEqual(actual,expected);self.assertEqual(len(actual),len(set(actual)))
        self.assertFalse(any(entry['status']=='complete' for entry in self.catalog['capabilities']))
    def test_unknown_conventions_duplicates_and_missing_links_rejected(self):
        for mutate in [lambda x:x['capabilities'].append(x['capabilities'][0]),lambda x:x['capabilities'][0].update(convention_ids=['absent']),lambda x:x['capabilities'][0].update(hp_menu_ids=['absent']),lambda x:x['hp_reference']['menus'].append(x['hp_reference']['menus'][0])]:
            value=copy.deepcopy(self.catalog);mutate(value)
            with self.assertRaises(ValueError):validate_catalog(value)
    def test_change_comparison_both_directions(self):
        changed=copy.deepcopy(self.catalog);removed=changed['capabilities'].pop();changed['capabilities'][0]['title']='Revised'
        extra=copy.deepcopy(removed);extra['id']='tool.new';changed['capabilities'].append(extra);changed['platform']='hp'
        changed['reference_cases']=[c for c in changed['reference_cases'] if c['capability_id']!=removed['id']]
        report=compare_catalogs(self.catalog,changed);reverse=compare_catalogs(changed,self.catalog)
        self.assertEqual(report['capabilities']['added'][0]['id'],'tool.new');self.assertEqual(report['capabilities']['removed'][0]['id'],removed['id'])
        self.assertEqual(report['capabilities']['added'],reverse['capabilities']['removed']);self.assertEqual(len(report['capabilities']['changed']),1)
        self.assertTrue(report['requires_review'])
    def test_source_change_requires_review_even_if_menus_same(self):
        after=build_catalog(('// no functional change proven\n'+SAMPLE).encode())
        diff=compare_catalogs(self.catalog,after)
        self.assertTrue(diff['source_hash_changed']);self.assertTrue(diff['requires_review']);self.assertEqual(diff['hp_menus']['changed'],[])
    def test_reference_case_changes_require_review(self):
        changed=copy.deepcopy(self.catalog);changed['reference_cases'][0]['expected']['origin']=5
        result=compare_catalogs(self.catalog,changed)
        self.assertTrue(result['requires_review']);self.assertEqual(len(result['reference_cases']['changed']),1)
    def test_reference_cases_run_and_fail_without_executing_code(self):
        from signallab_pc.reference_cases import run_cases
        document={'format':'signallab-reference-cases','schema_version':1,'cases':self.catalog['reference_cases']}
        result=run_cases(document);self.assertTrue(result['all_passed']);self.assertEqual(len(result['results']),5)
        document=copy.deepcopy(document);document['cases'][0]['expected']['origin']=99
        self.assertFalse(run_cases(document)['all_passed'])
        document['cases'][0]['operation']='__import__("os")'
        with self.assertRaises(ValueError):run_cases(document)
    def test_unchanged_catalog_no_changes(self):
        self.assertFalse(compare_catalogs(self.catalog,self.catalog)['requires_review'])
    def test_persistence_reference_hash_and_no_source_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.hppl';source.write_bytes(SAMPLE.encode());path=Path(folder)/'catalog.json'
            save_catalog(self.catalog,path);loaded=load_catalog(path);self.assertEqual(loaded,self.catalog)
            self.assertTrue(check_reference(source,loaded)['matches']);source.write_bytes((SAMPLE+'\n').encode())
            self.assertFalse(check_reference(source,loaded)['matches']);self.assertEqual(source.read_bytes(),(SAMPLE+'\n').encode())
    def test_dft_and_dtft_and_continuous_conventions_distinct(self):
        by_id={c['id']:c for c in self.catalog['capabilities']}
        self.assertIn('transform.dft.v1',by_id['tool.basic.dft']['convention_ids'])
        self.assertIn('transform.dtft.v1',by_id['tool.dtft_symbolic.0']['convention_ids'])
        self.assertIn('fourier.angular.v1',by_id['tool.fourier_symbolic.0']['convention_ids'])
        self.assertNotIn('transform.dft.v1',by_id['tool.fourier_symbolic.0']['convention_ids'])

if __name__=='__main__':unittest.main()
