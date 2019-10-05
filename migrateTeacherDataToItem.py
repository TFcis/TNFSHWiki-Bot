# -*- coding: utf-8 -*-
import argparse
import re
import json
import os

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


site = pywikibot.Site()
site.login()
datasite = site.data_repository()


class MigrateTeacherDataToItem:
    GENDER_QID = {
        '男': 'Q75',
        '女': 'Q76',
    }
    SUBJECT_QID = {
        '國文': 'Q46',
        '英文': 'Q47',
        '數學': 'Q48',
        '物理': 'Q49',
        '化學': 'Q50',
        '生物': 'Q51',
        '地理': 'Q52',
        '歷史': 'Q53',
        '公民': 'Q54',
        '地球科學': 'Q55',
        '生活科技': 'Q56',
        '資訊科技': 'Q57',
        '體育': 'Q58',
        '音樂': 'Q59',
        '美術': 'Q60',
        '家政': 'Q61',
        '健康與護理': 'Q62',
        '全民國防': 'Q63',
    }
    JOBS_QID = {
        '圖書館主任': 'Q78',
        '社團活動組組長': 'Q91',
        '特教組長': 'Q113',
        '總務主任': 'Q128',
    }
    LIVE_QID = {
        '現任': 'Q64',
        '離任': 'Q65',
        '退休': 'Q86',
        '已退休': 'Q86',
    }
    YEAR_QID = {
        103: 'Q74',
        104: 'Q73',
        105: 'Q72',
        106: 'Q71',
        107: 'Q70',
        108: 'Q64',
    }

    def __init__(self, title):
        self.title = title
        self.page = pywikibot.Page(site, title)

        self.gender = self._get_tem_val(self.page.text, 'gender')
        self.subject = self._get_tem_val(self.page.text, 'subject')
        self.jobs = self._get_tem_val(self.page.text, 'jobs')
        self.classes = self._get_tem_val(self.page.text, 'class')
        self.live = self._get_tem_val(self.page.text, 'live')
        self.nickname = self._get_tem_val(self.page.text, 'nickname')
        self.edustatus = self._get_tem_val(self.page.text, 'edustatus')
        self.education = self._get_tem_val(self.page.text, 'education')

        self.gender_id = self._parse_gender(self.gender)
        self.subject_id = self._parse_subject(self.subject)
        self.jobs_id = self._parse_jobs(self.jobs)
        self.class_id = self._parse_class(self.classes)
        self.live_id = self._parse_live(self.live)
        self.nickname = self._parse_nickname(self.nickname)
        self.edustatus = self._parse_edustatus(self.edustatus)
        self._parse_education(self.education)

        print('gender', self.gender, self.gender_id)
        print('subject', self.subject, self.subject_id)
        print('jobs', self.jobs)
        print('classes', self.classes)
        print('live', self.live, self.live_id)
        print('nickname', self.nickname)
        print('edustatus', self.edustatus)

    def save(self):
        # Init empty item
        data = {
            'labels': {},
            'sitelinks': {},
            'claims': [],
        }

        # Set lebels
        data['labels']['zh-tw'] = {
            'language': 'zh-tw',
            'value': self.title
        }

        # Set sitelinks
        data['sitelinks']['tnfshwiki'] = {
            'site': 'tnfshwiki',
            'title': self.title,
        }

        # 性質
        new_claim = pywikibot.page.Claim(datasite, 'P1')
        new_claim.setTarget(pywikibot.ItemPage(datasite, 'Q67'))  # 老師
        data['claims'].append(new_claim.toJSON())

        # 性別
        if self.gender_id:
            new_claim = pywikibot.page.Claim(datasite, 'P31')
            new_claim.setTarget(pywikibot.ItemPage(datasite, self.gender_id))
            data['claims'].append(new_claim.toJSON())

        # 科目
        if self.subject_id:
            new_claim = pywikibot.page.Claim(datasite, 'P21')
            new_claim.setTarget(pywikibot.ItemPage(datasite, self.subject_id))
            data['claims'].append(new_claim.toJSON())

        # 行政職位
        if self.jobs_id:
            new_claim = pywikibot.page.Claim(datasite, 'P28')
            new_claim.setTarget(pywikibot.ItemPage(datasite, self.jobs_id[0]))
            if self.jobs_id[1]:
                qualifier = pywikibot.page.Claim(datasite, 'P27')  # 學年度
                qualifier.setTarget(pywikibot.ItemPage(datasite, self.YEAR_QID[self.jobs_id[1]]))
                new_claim.addQualifier(qualifier)
            data['claims'].append(new_claim.toJSON())

        # 導師
        for class1 in self.class_id:
            new_claim = pywikibot.page.Claim(datasite, 'P25')
            new_claim.setTarget(class1[0])
            qualifier = pywikibot.page.Claim(datasite, 'P27')  # 學年度
            qualifier.setTarget(pywikibot.ItemPage(datasite, self.YEAR_QID[class1[1]]))
            new_claim.addQualifier(qualifier)
            data['claims'].append(new_claim.toJSON())

        # 任職狀況
        if self.live_id:
            new_claim = pywikibot.page.Claim(datasite, 'P22')
            new_claim.setTarget(pywikibot.ItemPage(datasite, self.live_id))
            data['claims'].append(new_claim.toJSON())

        # 別稱
        for nickname in self.nickname:
            new_claim = pywikibot.page.Claim(datasite, 'P30')
            new_claim.setTarget(nickname)
            data['claims'].append(new_claim.toJSON())

        # 學歷
        for status in self.edustatus:
            new_claim = pywikibot.page.Claim(datasite, 'P29')
            new_claim.setTarget(status)
            data['claims'].append(new_claim.toJSON())

        print(json.dumps(data['labels'], indent=4, ensure_ascii=False))
        for claim in data['claims']:
            print(claim['mainsnak']['property'],
                  claim['mainsnak']['datatype'],
                  claim['mainsnak']['datavalue'])

        summary = '從[[{}]]匯入老師資料'.format(self.title)
        input('Create item with summary: {}'.format(summary))
        item = datasite.editEntity({}, data, summary=summary)
        print(item['entity']['id'])
        newitemid = item['entity']['id']

        text = self.page.text
        text = re.sub(r'{{簡介 老師[\s\S]+?}}\n*', r'{{老師資訊框}}\n', text)
        text = re.sub(r'{{Expand\|.+}}\n*', '', text)
        pywikibot.showDiff(self.page.text, text)
        summary = '資料已匯入至[[Item:{}]]'.format(newitemid)
        print('Save with summary: {}'.format(summary))
        self.page.text = text
        self.page.save(summary=summary, minor=False, asynchronous=True)

    def _get_tem_val(self, text, key):
        m = re.search(r'[\s\S]*\|\s*{}\s*=\s*([^|}}]*?)\s*(\||}}}})'.format(key), text)
        if m:
            return m.group(1)
        return None

    def _parse_gender(self, gender):
        if not gender:
            return None
        return self.GENDER_QID[gender]

    def _parse_subject(self, subject):
        if not subject:
            return None
        return self.SUBJECT_QID[subject]

    def _parse_class(self, classes):
        if not classes:
            return []
        if re.search(r'^(否|無|是)(（\d+學年度）)?$', classes):
            return []

        classes = re.sub(r'<br\s*/?>', '\n', classes)
        classes = re.sub(r'\n\n+', '\n', classes)
        classes = classes.split('\n')
        result = []
        for class1 in classes:
            m = re.search(r'^(\d+)（(\d+)學年度）$', class1)
            if m:
                result.append((m.group(1), int(m.group(2))))
            else:
                raise Exception('Cannot parse {}'.format(class1))
        return result

    def _parse_jobs(self, jobs):
        if not jobs:
            return None
        if jobs in self.LIVE_QID:
            self.jobs = ''
            if not self.live:
                self.live = jobs
            return None
        if re.search(r'^.{2,5}科專任教師（\d+學年度）$', jobs):
            return None
        if re.search(r'^.{2,5}科專任教師兼(\d+)?(班導|導師)（\d+學年度）$', jobs):
            return None
        if re.search(r'^(無|退休教師|已退休.*)$', jobs):
            return None
        m = re.search(r'^.{2,5}科專任教師兼(?:.{2}處)?(.*)（(\d+)學年度）$', jobs)
        year = None
        if m:
            jobs = m.group(1)
            year = int(m.group(2))
        return (self.JOBS_QID[jobs], year)

    def _parse_live(self, live):
        if not live:
            return None
        return self.LIVE_QID[live]

    def _parse_nickname(self, nickname):
        if not nickname:
            return []
        nickname = re.sub(r'、', '\n', nickname)
        nickname = re.sub(r'<br\s*/?>', '\n', nickname)
        nickname = re.sub(r'\n\n+', '\n', nickname)
        return nickname.split('\n')

    def _parse_edustatus(self, edustatus):
        if not edustatus:
            return []
        edustatus = re.sub(r'<br\s*/?\s*>', '\n', edustatus)
        edustatus = re.sub(r'\n\n+', '\n', edustatus)
        edustatus = edustatus.split('\n')
        return edustatus

    def _parse_education(self, education):
        if not education:
            return []
        if '是' in education:
            self.edustatus.append('國立臺南第一高級中學')


def main():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        MigrateTeacherDataToItem(args.title).save()
