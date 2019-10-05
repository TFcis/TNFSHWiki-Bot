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
    }
    LIVE_QID = {
        '現任': 'Q64',
        '離任': 'Q65',
    }

    def main(self, title):
        page = pywikibot.Page(site, title)

        gender = self._get_tem_val(page.text, 'gender')
        subject = self._get_tem_val(page.text, 'subject')
        jobs = self._get_tem_val(page.text, 'jobs')
        classes = self._get_tem_val(page.text, 'class')
        live = self._get_tem_val(page.text, 'live')
        nickname = self._get_tem_val(page.text, 'nickname')
        education = self._get_tem_val(page.text, 'education')

        gender_id = self._parse_gender(gender)
        subject_id = self._parse_subject(subject)
        jobs_id = self._parse_jobs(jobs)
        live_id = self._parse_live(live)

        print('gender', gender, gender_id)
        print('subject', subject, subject_id)
        print('jobs', jobs)
        print('classes', classes)
        print('live', live, live_id)
        print('nickname', nickname)
        print('education', education)

        # Init empty item
        data = {
            'labels': {},
            'sitelinks': {},
            'claims': [],
        }

        # Set lebels
        data['labels']['zh-tw'] = {
            'language': 'zh-tw',
            'value': title
        }

        # Set sitelinks
        data['sitelinks']['tnfshwiki'] = {
            'site': 'tnfshwiki',
            'title': title,
        }

        # 性質
        new_claim = pywikibot.page.Claim(datasite, 'P1')
        new_claim.setTarget(pywikibot.ItemPage(datasite, 'Q67'))  # 老師
        data['claims'].append(new_claim.toJSON())

        # 性別
        if gender_id:
            new_claim = pywikibot.page.Claim(datasite, 'P31')
            new_claim.setTarget(pywikibot.ItemPage(datasite, gender_id))
            data['claims'].append(new_claim.toJSON())

        # 科目
        if subject_id:
            new_claim = pywikibot.page.Claim(datasite, 'P21')
            new_claim.setTarget(pywikibot.ItemPage(datasite, subject_id))
            data['claims'].append(new_claim.toJSON())

        # 行政職位
        if jobs_id:
            new_claim = pywikibot.page.Claim(datasite, 'P28')
            new_claim.setTarget(pywikibot.ItemPage(datasite, jobs_id))
            data['claims'].append(new_claim.toJSON())

        # 導師
        if classes:
            new_claim = pywikibot.page.Claim(datasite, 'P25')
            new_claim.setTarget(pywikibot.ItemPage(datasite, classes))
            data['claims'].append(new_claim.toJSON())

        # 任職狀況
        if live_id:
            new_claim = pywikibot.page.Claim(datasite, 'P22')
            new_claim.setTarget(pywikibot.ItemPage(datasite, live_id))
            data['claims'].append(new_claim.toJSON())

        # 別稱
        if nickname:
            new_claim = pywikibot.page.Claim(datasite, 'P30')
            new_claim.setTarget(pywikibot.ItemPage(datasite, nickname))
            data['claims'].append(new_claim.toJSON())

        # 校友
        if education:
            new_claim = pywikibot.page.Claim(datasite, 'P21')
            new_claim.setTarget(pywikibot.ItemPage(datasite, education))
            data['claims'].append(new_claim.toJSON())

        print(json.dumps(data['labels'], indent=4, ensure_ascii=False))
        for claim in data['claims']:
            print(claim['mainsnak']['property'],
                  claim['mainsnak']['datatype'],
                  claim['mainsnak']['datavalue'])

        summary = '從[[{}]]匯入老師資料'.format(title)
        input('Create item with summary: {}'.format(summary))
        item = datasite.editEntity({}, data, summary=summary)
        print(item['entity']['id'])
        newitemid = item['entity']['id']

        text = page.text
        text = re.sub(r'{{簡介 老師[\s\S]+?}}\n*', r'{{老師資訊框}}\n', text)
        pywikibot.showDiff(page.text, text)
        summary = '資料已匯入至[[Item:{}]]'.format(newitemid)
        input('Save with summary: {}'.format(summary))
        page.text = text
        page.save(summary=summary, minor=False)

    def _get_tem_val(self, text, key):
        m = re.search(r'\|\s*{}\s*=\s*([^|\n}}]*?)\s*(\||\n|}}}})'.format(key), text)
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

    def _parse_jobs(self, jobs):
        if not jobs:
            return None
        return self.JOBS_QID[jobs]

    def _parse_live(self, live):
        if not live:
            return None
        return self.LIVE_QID[live]


def main():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('title', nargs='?')
    args = parser.parse_args()
    if args.title is None:
        main()
    else:
        MigrateTeacherDataToItem().main(args.title)
