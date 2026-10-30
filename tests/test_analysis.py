import hashlib
import math
import pytest
from app.analysis import DataError, MAX_BYTES, parse_csv, preview, analyze, calculate, number


@pytest.mark.parametrize('text,expected', [('0',0),('-2.5',-2.5),('.5',.5),('1.',1),('+2',2),('1e3',1000),('-1.25E-2',-.0125),('5e-324',5e-324)])
def test_decimal_values(text, expected):
    assert number(text) == expected


@pytest.mark.parametrize('text', ['NaN','nan','Infinity','-inf','1e309','0x10','1_000','1,25','2d','',' 2','١٢'])
def test_invalid_decimal_values(text):
    assert number(text) is None


def test_independent_temperature_reference():
    r = calculate([20.,22.,24.,26.,28.])
    assert r == pytest.approx(dict(count=5, minimum=20, maximum=28, mean=24, median=24, sampleStandardDeviation=math.sqrt(10)))


@pytest.mark.parametrize('values,mean,median,sd', [([1,2,3,4],2.5,2.5,math.sqrt(5/3)),([-4,-2,0],-2,-2,2),([7,7,7],7,7,0),([1e15,1e15+2,1e15+4],1e15+2,1e15+2,2)])
def test_reference_statistics(values, mean, median, sd):
    r = calculate(values)
    assert r['mean'] == mean
    assert r['median'] == median
    assert r['sampleStandardDeviation'] == pytest.approx(sd)


def test_single_value_has_no_sample_deviation():
    assert calculate([8.])['sampleStandardDeviation'] is None


def test_large_even_median_does_not_overflow():
    assert calculate([1e308,1e308])['median'] == 1e308


def test_subnormal_even_median_does_not_underflow():
    assert calculate([5e-324,5e-324])['median'] == 5e-324


def test_large_opposite_values_reject_unrepresentable_deviation():
    with pytest.raises(DataError): calculate([-1.7e308,1.7e308])


def test_empty_sample_rejected():
    with pytest.raises(DataError): calculate([])


def test_bom_quotes_multiline_blank_lines_and_hash():
    raw = '\ufeffsite,value,note\r\n"A,B",2,"two\nlines"\r\n\r\nC,4,ok\r\n'.encode('utf-8')
    d = parse_csv(raw)
    assert d.rows == (('A,B','2','two\nlines'),('C','4','ok'))
    assert d.sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('raw', [b'',b'\n\n',b'a,b\n',b'a,a\n1,2',b'a, \n1,2',b'a,b\n1',b'a,b\n1,2,3',b'a\n"unterminated',b'a\n\xff',b'a\n\x00'])
def test_malformed_csv_rejected(raw):
    with pytest.raises(DataError): parse_csv(raw)


def test_missing_values_and_logical_records():
    d = parse_csv(b'site,value\na,20\nb,\nc,24\n')
    r = analyze(d,'s.csv','value',' C ','test')
    assert r['excludedBlankValues'] == 1
    assert r['totalRows'] == 3
    assert [m['recordNumber'] for m in r['measurements']] == [2,4]
    assert r['statistics']['mean'] == 22
    assert r['unit'] == 'C'


def test_preview_is_bounded_and_finds_numeric_columns():
    d = parse_csv(('site,value,blank\n' + 'A,2,\n'*25).encode())
    r = preview(d,'s.csv')
    assert r['numericColumns'] == ['value']
    assert r['rowCount'] == 25
    assert len(r['previewRows']) == 20


@pytest.mark.parametrize('column,unit', [('absent',''),('v','x'*33),('v','a\tb')])
def test_analysis_contract(column,unit):
    with pytest.raises(DataError): analyze(parse_csv(b'v\n1\n'),'s.csv',column,unit,'test')


def test_invalid_measurement_identifies_logical_record():
    with pytest.raises(DataError, match="record 3.*column 'v'"):
        analyze(parse_csv(b'v\n1\nbad\n'),'s.csv','v','','test')


def test_blank_only_column_rejected():
    with pytest.raises(DataError, match='no measurements'):
        analyze(parse_csv(b'site,v\nA,\n'),'s.csv','v','','test')


def test_byte_limit():
    with pytest.raises(DataError) as e: parse_csv(b'x'*(MAX_BYTES+1))
    assert e.value.status_code == 413


@pytest.mark.parametrize('raw', [('a\n'+'1\n'*10001).encode(),(','.join('h'+str(i) for i in range(51))+'\n').encode(),('a\n'+'x'*2001).encode()])
def test_record_column_field_limits(raw):
    with pytest.raises(DataError): parse_csv(raw)


def test_exact_row_and_field_limits_accepted():
    assert len(parse_csv(('a\n'+'1\n'*10000).encode()).rows) == 10000
    assert len(parse_csv(('a\n'+'x'*2000).encode()).rows[0][0]) == 2000
