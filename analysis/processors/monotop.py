#!/usr/bin/env python
import lz4.frame as lz4f
import cloudpickle
import json
import pprint
import numpy as np
import awkward
np.seterr(divide='ignore', invalid='ignore', over='ignore')
from coffea.arrays import Initialize
from coffea import hist, processor
from coffea.util import load, save
from optparse import OptionParser

class AnalysisProcessor(processor.ProcessorABC):
    def __init__(self, year, columns, xsec, lumi, triggers, corrections, ids, metfilters):
        self._columns = columns
        self._year = year
        self._xsec = xsec
        self._lumi = lumi
        self._triggers = triggers
        self._corrections = corrections
        self._ids = ids
        self._metfilters = metfilters

        self._samples = {
            "hadronic":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','MET'),
            "isoneM":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','MET'),
            "istwoM":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','MET'),
            "isoneE":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','SingleElectron','EGamma'),
            "istwoE":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','SingleElectron','EGamma')
            # "hadronic":('ZJets','WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','MET','Mhs_50','Mhs_70','Mhs_90','MonoJet','MonoW','MonoZ'),
            # "leptonicM":('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','MET'),
            # "leptonicE":('WJets','DY','TT','ST','WW','WZ','ZZ','QCD','HToBB','SingleElectron','EGamma'),
            # "istwoM":('WJets','DY','TT','ST','WW','WZ','ZZ','HToBB','MET'),
            # "istwoE":('WJets','DY','TT','ST','WW','WZ','ZZ','HToBB','SingleElectron','EGamma'),
            # "isoneA":('GJets','QCD','SinglePhoton','EGamma')
        }

        self._e_id = {}
        self._e_id['2016'] = {}
        self._e_id['2016']['loose_id'] = 'Electron_cutBased'
        self._e_id['2016']['tight_id'] = 'Electron_cutBased'
        self._e_id['2016']['dxy'] = 'Electron_dxy'
        self._e_id['2016']['dz'] = 'Electron_dz'
        self._e_id['2016']['iso'] = 'Null'
        self._e_id['2017'] = self._e_id['2016']
        self._e_id['2018'] = self._e_id['2016']

        self._mu_id = {}
        self._mu_id['2016'] = {}
        self._mu_id['2016']['iso'] = 'Muon_pfRelIso04_all'
        self._mu_id['2016']['tight_id'] = 'Muon_tightId'
        self._mu_id['2016']['med_id'] = 'Muon_mediumId'
        self._mu_id['2016']['dxy'] = 'Muon_dxy'
        self._mu_id['2016']['dz'] = 'Muon_dz'
        self._mu_id['2017'] = self._mu_id['2016']
        self._mu_id['2018'] = self._mu_id['2016']

        self._tau_id = {}
        self._tau_id['2016'] = {}
        self._tau_id['2016']['id'] = 'Tau_idMVAoldDM2017v2'
        self._tau_id['2016']['decayMode'] = 'Tau_idDecayMode'
        self._tau_id['2017'] = self._tau_id['2016']
        self._tau_id['2018'] = self._tau_id['2016']

        self._pho_id = {}
        self._pho_id['2016'] = {}
        self._pho_id['2016']['loose_id'] = 'Photon_cutBased'
        self._pho_id['2016']['tight_id'] = 'Photon_cutBased'
        self._pho_id['2016']['eleveto']  = 'Photon_electronVeto'
        self._pho_id['2016']['phoeta']   = 'Photon_eta'
        self._pho_id['2017'] = self._pho_id['2016']
        self._pho_id['2017']['loose_id'] = 'Photon_cutBasedBitmap'
        self._pho_id['2017']['tight_id'] = 'Photon_cutBasedBitmap'
        self._pho_id['2018'] = self._pho_id['2017']

        self._fj_id = {}
        self._fj_id['2016'] = {}
        self._fj_id['2016']['id'] = 'AK15Puppi_jetId'
        self._fj_id['2017'] = self._fj_id['2016']
        self._fj_id['2018'] = self._fj_id['2016']


        self._j_id = {}
        self._j_id['2016'] = {}
        self._j_id['2016']['id'] = 'Jet_jetId'
        self._j_id['2016']['nhf'] = 'Jet_neHEF'
        self._j_id['2016']['nef'] = 'Jet_neEmEF'
        self._j_id['2016']['chf'] = 'Jet_chHEF'
        self._j_id['2016']['cef'] = 'Jet_chEmEF'
        self._j_id['2017'] =  self._j_id['2016']
        self._j_id['2018'] =  self._j_id['2016']

        self._deep = {}
        self._deep['2016'] = {}
        self._deep['2016']['probTbcq'] ='AK15Puppi_probTbcq'
        self._deep['2016']['probTbqq'] ='AK15Puppi_probTbqq'
        self._deep['2016']['probTbc'] ='AK15Puppi_probTbc'
        self._deep['2016']['probTbq'] ='AK15Puppi_probTbq'
        self._deep['2016']['probWcq'] ='AK15Puppi_probWcq'
        self._deep['2016']['probWqq'] ='AK15Puppi_probWqq'
        self._deep['2016']['probZbb'] ='AK15Puppi_probZbb'
        self._deep['2016']['probZcc'] ='AK15Puppi_probZcc'
        self._deep['2016']['probZqq'] ='AK15Puppi_probZqq'
        self._deep['2016']['probHbb'] ='AK15Puppi_probHbb'
        self._deep['2016']['probHcc'] ='AK15Puppi_probHcc'
        self._deep['2016']['probHqqqq'] ='AK15Puppi_probHqqqq'
        self._deep['2016']['probQCDbb'] ='AK15Puppi_probQCDbb'
        self._deep['2016']['probQCDcc'] ='AK15Puppi_probQCDcc'
        self._deep['2016']['probQCDb'] ='AK15Puppi_probQCDb'
        self._deep['2016']['probQCDc'] ='AK15Puppi_probQCDc'
        self._deep['2016']['probQCDothers'] ='AK15Puppi_probQCDothers'
        self._deep['2017'] = self._deep['2016']
        self._deep['2018'] = self._deep['2016']

        self._accumulator = processor.dict_accumulator({
            'sumw': hist.Hist("sumw", hist.Cat("dataset", "Primary dataset"), hist.Bin("sumw", "Weight value", [0.])),
            'CaloMinusPfOverRecoil': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("CaloMinusPfOverRecoil","Calo - Pf / Recoil",35,0,1)),
            'recoil': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("recoil","Hadronic Recoil",[250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'mindphi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("mindphi","Min dPhi(MET,AK4s)",30,0,3.5)),
            'diledphi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("diledphi","Min dPhi(Dileptons,AK4s)",30,0,3.5)),
            'ledphi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ledphi","Min dPhi(lepton,AK4s)",30,0,3.5)),
            'j1pt': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("j1pt","AK4 Leading Jet Pt",[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'j1eta': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("j1eta","AK4 Leading Jet Eta",35,-3.5,3.5)),
            'j1phi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("j1phi","AK4 Leading Jet Phi",35,-3.5,3.5)),
            'fj1pt': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("fj1pt","AK15 Leading Jet Pt",[200.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'fj1eta': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("fj1eta","AK15 Leading Jet Eta",35,-3.5,3.5)),
            'fj1phi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("fj1phi","AK15 Leading Jet Phi",35,-3.5,3.5)),
            'njets': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("njets","AK4 Number of Jets",6,0,5)),
            'ndcsvL': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndcsvL","AK4 Number of deepCSV Loose Jets",6,0,5)),
            'ndflvL': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndflvL","AK4 Number of deepFlavor Loose Jets",6,0,5)),
            'ndcsvM': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndcsvM","AK4 Number of deepCSV Medium Jets",6,0,5)),
            'ndflvM': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndflvM","AK4 Number of deepFlavor Medium Jets",6,0,5)),
            'ndcsvT': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndcsvT","AK4 Number of deepCSV Tight Jets",6,0,5)),
            'ndflvT': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("ndflvT","AK4 Number of deepFlavor Tight Jets",6,0,5)),
            'nfjtot': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("nfjtot","AK15 Number of Jets",4,0,3)),
            'nfjgood': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("nfjgood","AK15 Number of Good Jets",4,0,3)),
            'nfjclean': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("nfjclean","AK15 Number of cleaned Jets",4,0,3)),
            'fjmass': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("fjmass","AK15 Jet Mass",[0.0, 40.0, 60.0, 75.0, 85.0, 115.0, 135.0, 225.0, 500.0])),
            'e1pt': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("e1pt","Leading Electron Pt",[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'e1eta': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("e1eta","Leading Electron Eta",48,-2.4,2.4)),
            'e1phi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("e1phi","Leading Electron Phi",64,-3.2,3.2)),
            'e1drj': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("e1drj","ΔR between Leading Electron and Leading Jet ",25,0,5)),
            'dielemass': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("dielemass","Dielectron mass",60,60,120)),
            'mu1pt': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("mu1pt","Leading Muon Pt",[30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0])),
            'mu1eta': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("mu1eta","Leading Muon Eta",48,-2.4,2.4)),
            'mu1phi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("mu1phi","Leading Muon Phi",64,-3.2,3.2)),
            'mu1drj': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("mu1drj","ΔR between Leading Muon and Leading Jet ",25,0,5)),
            'dimumass': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("dimumass","Dimuon mass",60,60,120)),
            'TopTagger': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("TopTagger","TopTagger",15,0,1)),
            'DarkHiggsTagger': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("DarkHiggsTagger","DarkHiggsTagger",15,0,1)),
            'VvsQCDTagger': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("VvsQCDTagger","VvsQCDTagger",15,0,1)),
            'probTbcq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probTbcq","probTbcq",15,0,1)),
            'probTbqq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probTbqq","probTbqq",15,0,1)),
            'probTbc': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probTbc","probTbc",15,0,1)),
            'probTbq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probTbq","probTbq",15,0,1)),
            'probWcq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probWcq","probWcq",15,0,1)),
            'probWqq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probWqq","probWqq",15,0,1)),
            'probZbb': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probZbb","probZbb",15,0,1)),
            'probZcc': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probZcc","probZcc",15,0,1)),
            'probZqq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probZqq","probZqq",15,0,1)),
            'probHbb': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probHbb","probHbb",15,0,1)),
            'probHcc': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probHcc","probHcc",15,0,1)),
            'probHqqqq': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probHqqqq","probHqqqq",15,0,1)),
            'probQCDbb': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probQCDbb","probQCDbb",15,0,1)),
            'probQCDcc': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probQCDcc","probQCDcc",15,0,1)),
            'probQCDb': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probQCDb","probQCDb",15,0,1)),
            'probQCDc': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probQCDc","probQCDc",15,0,1)),
            'probQCDothers': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("probQCDothers","probQCDothers",15,0,1)),
            'recoilVSmindphi': hist.Hist("Events", hist.Cat("dataset", "Primary dataset"), hist.Cat("category", "Category"), hist.Cat("control_region", "Control Region"), hist.Bin("recoil","Hadronic Recoil",[250.0, 280.0, 310.0, 340.0, 370.0, 400.0, 430.0, 470.0, 510.0, 550.0, 590.0, 640.0, 690.0, 740.0, 790.0, 840.0, 900.0, 960.0, 1020.0, 1090.0, 1160.0, 1250.0]), hist.Bin("mindphi","Min dPhi(MET,AK4s)",30,0,3.5)),

        })

    @property
    def accumulator(self):
        return self._accumulator

    @property
    def columns(self):
        return self._columns

    def process(self, df):

            dataset = df['dataset']

            selected_regions = {}
            if not dataset in selected_regions: selected_regions[dataset] = []
            for selection,v in self._samples.items():
                for i in range (0,len(v)):
                    if v[i] not in dataset: continue
                    selected_regions[dataset].append(selection)

            ###
            #Getting corrections, ids, triggers, ecc, from .coffea files
            ###

            met_trigger_paths       = self._triggers['met_trigger_paths']
            singleele_trigger_paths = self._triggers['singleele_trigger_paths']
            singlepho_trigger_paths = self._triggers['singlepho_trigger_paths']

            get_ttbar_weight        = self._corrections['get_ttbar_weight']
            get_nlo_weight          = self._corrections['get_nlo_weight']
            get_adhoc_weight        = self._corrections['get_adhoc_weight']
            get_pu_weight           = self._corrections['get_pu_weight']
            get_met_trig_weight     = self._corrections['get_met_trig_weight']
            get_met_zmm_trig_weight = self._corrections['get_met_zmm_trig_weight']
            get_ele_trig_weight     = self._corrections['get_ele_trig_weight']
            get_pho_trig_weight     = self._corrections['get_pho_trig_weight']
            get_ecal_bad_calib      = self._corrections['get_ecal_bad_calib']

            isLooseElectron = self._ids['isLooseElectron']
            isTightElectron = self._ids['isTightElectron']
            isLooseMuon     = self._ids['isLooseMuon']
            isTightMuon     = self._ids['isTightMuon']
            isLooseTau      = self._ids['isLooseTau']
            isLoosePhoton   = self._ids['isLoosePhoton']
            isTightPhoton   = self._ids['isTightPhoton']
            isGoodJet       = self._ids['isGoodJet']
            isGoodFatJet    = self._ids['isGoodFatJet']
            isHEMJet        = self._ids['isHEMJet']

            met_filter_flags = self._metfilters['met_filter_flags']

            ###
            #Initialize global quantities (MET ecc.)
            ###

            met = Initialize({'pt':df['MET_pt'],
                              'eta':0,
                              'phi':df['MET_phi'],
                              'mass':0})

            calomet = Initialize({'pt':df['CaloMET_pt'],
                                  'eta':0,
                                  'phi':df['CaloMET_phi'],
                                  'mass':0})

            ###
            #Initialize physics objects
            ###

            #Define first and empty object that will use as protection against arrays with size 0
            #Will use MET to set the correct size for the arrays
            #Not used at the moment

            #empty_jagged = awkward.JaggedArray.fromcounts(np.ones_like(met.pt, dtype=int),np.zeros_like(met.pt))
            #empty_obj = Initialize({'pt':empty_jagged,
            #                        'eta':empty_jagged,
            #                        'phi':empty_jagged,
            #                        'mass':empty_jagged})

            e = Initialize({'pt':df['Electron_pt'],
                            'eta':df['Electron_eta'],
                            'phi':df['Electron_phi'],
                            'mass':df['Electron_mass']})

            for key in self._e_id[self._year]:
                e[key] = e.pt.zeros_like()
                if self._e_id[self._year][key] in df:
                    e[key] = df[self._e_id[self._year][key]]

            e['isloose'] = isLooseElectron(e.pt,e.eta,e.dxy,e.dz,e.iso,e.loose_id,self._year)
            e['istight'] = isTightElectron(e.pt,e.eta,e.dxy,e.dz,e.iso,e.tight_id,self._year)

            leading_e = e[e.pt.argmax()]
            leading_e = leading_e[leading_e.istight.astype(np.bool)]

            e_loose = e[e.isloose.astype(np.bool)]
            e_tight = e[e.istight.astype(np.bool)]

            e_ntot = e.counts
            e_nloose = e_loose.counts
            e_ntight = e_tight.counts

            mu = Initialize({'pt':df['Muon_pt'],
                             'eta':df['Muon_eta'],
                             'phi':df['Muon_phi'],
                             'mass':df['Muon_mass']})

            for key in self._mu_id[self._year]:
                mu[key] = mu.pt.zeros_like()
                if self._mu_id[self._year][key] in df:
                    mu[key] = df[self._mu_id[self._year][key]]

            mu['isloose'] = isLooseMuon(mu.pt,mu.eta,mu.dxy,mu.dz,mu.iso,mu.med_id,self._year)
            mu['istight'] = isTightMuon(mu.pt,mu.eta,mu.dxy,mu.dz,mu.iso,mu.tight_id,self._year)

            leading_mu = mu[mu.pt.argmax()]
            leading_mu = leading_mu[leading_mu.istight.astype(np.bool)]

            mu_loose=mu[mu.isloose.astype(np.bool)]
            mu_tight=mu[mu.istight.astype(np.bool)]

            mu_ntot = mu.counts
            mu_nloose = mu_loose.counts
            mu_ntight = mu_tight.counts

            tau = Initialize({'pt':df['Tau_pt'],
                              'eta':df['Tau_eta'],
                              'phi':df['Tau_phi'],
                              'mass':df['Tau_mass']})

            for key in self._tau_id[self._year]:
                tau[key] = tau.pt.zeros_like()
                if self._tau_id[self._year][key] in df:
                    tau[key] = df[self._tau_id[self._year][key]]


            tau['isclean'] =~tau.match(mu_loose,0.3)&~tau.match(e_loose,0.3)
            tau['isloose']=isLooseTau(tau.pt,tau.eta,tau.decayMode,tau.id,self._year)&tau.isclean.astype(np.bool)
            tau_loose=tau[tau.isloose.astype(np.bool)]

            tau_ntot=tau.counts
            tau_nloose=tau_loose.counts

            pho = Initialize({'pt':df['Photon_pt'],
                              'eta':df['Photon_eta'],
                              'phi':df['Photon_phi'],
                              'mass':df['Photon_mass']})

            for key in self._pho_id[self._year]:
                pho[key] = pho.pt.zeros_like()
                if self._pho_id[self._year][key] in df:
                    pho[key] = df[self._pho_id[self._year][key]]

            pho['isclean'] =~pho.match(e_loose,0.4)
            pho['isloose']=isLoosePhoton(pho.pt,pho.eta,pho.loose_id,pho.eleveto,self._year)&pho.isclean.astype(np.bool)
            pho['istight']=isTightPhoton(pho.pt,pho.eta,pho.tight_id,pho.eleveto,self._year)&pho.isclean.astype(np.bool)

            leading_pho = pho[pho.pt.argmax()]
            leading_pho = leading_pho[leading_pho.istight.astype(np.bool)]

            pho_loose=pho[pho.isloose.astype(np.bool)]
            pho_tight=pho[pho.istight.astype(np.bool)]

            pho_ntot=pho.counts
            pho_nloose=pho_loose.counts
            pho_ntight=pho_tight.counts

            fj = Initialize({'pt':df['AK15Puppi_pt'],
                             'eta':df['AK15Puppi_eta'],
                             'phi':df['AK15Puppi_phi'],
                             'mass':df['AK15Puppi_mass']})

            fj['msd'] = df['AK15Puppi_msoftdrop']

            for key in self._fj_id[self._year]:
                fj[key] = fj.pt.zeros_like()
                if self._fj_id[self._year][key] in df:
                    fj[key] = df[self._fj_id[self._year][key]]

            fj['isgood'] = isGoodFatJet(fj.pt, fj.eta, fj.id)
            fj['isclean'] =~fj.match(pho_loose,1.5)&~fj.match(mu_loose,1.5)&~fj.match(e_loose,1.5)&fj.isgood.astype(np.bool)

            for key in self._deep[self._year]:
                fj[key] = fj.pt.zeros_like()
                if self._deep[self._year][key] in df:
                    fj[key] = df[self._deep[self._year][key]]

            #fj['probQCD'] = fj.probQCDbb+fj.probQCDcc+fj.probQCDb+fj.probQCDc+fj.probQCDothers
            fj['TopTagger'] = fj.probTbcq+fj.probTbqq
            fj['DarkHiggsTagger'] = fj.probZbb + fj.probHbb #/ (fj.probZbb+fj.probHbb+fj.probWcq+fj.probWqq+fj.probZcc+fj.probZqq+fj.probHcc+fj.probHqqqq+fj.probQCD)
            fj['VvsQCDTagger'] = (fj.probWcq+fj.probWqq+fj.probZcc+fj.probZqq) / (fj.probWcq+fj.probWqq+fj.probZcc+fj.probZqq+fj.probQCDothers+fj.probQCDcc)

            leading_fj = fj[fj.pt.argmax()]
            leading_fj = leading_fj[leading_fj.isclean.astype(np.bool)]

            fj_good = fj[fj.isgood.astype(np.bool)]
            fj_clean=fj[fj.isclean.astype(np.bool)]

            fj_ntot=fj.counts
            fj_ngood=fj_good.counts
            fj_nclean=fj_clean.counts

            j = Initialize({'pt':df['Jet_pt'],
                            'eta':df['Jet_eta'],
                            'phi':df['Jet_phi'],
                            'mass':df['Jet_mass']})

            #https://twiki.cern.ch/twiki/bin/viewauth/CMS/BtagRecommendation102X
            j['deepcsv'] = df['Jet_btagDeepB']
            j['deepflv'] = df['Jet_btagDeepFlavB']

            for key in self._j_id[self._year]:
                j[key] = j.pt.zeros_like()
                if self._j_id[self._year][key] in df:
                    j[key] = df[self._j_id[self._year][key]]

            j['isgood'] = isGoodJet(j.pt, j.eta, j.id, j.nhf, j.nef, j.chf, j.cef)
            j['isHEM'] = isHEMJet(j.pt, j.eta, j.phi)
            j['isclean'] = ~j.match(e_loose,0.4)&~j.match(mu_loose,0.4)&~j.match(pho_loose,0.4)&j.isgood.astype(np.bool)
            #j['isclean'] = ~j.match(e_tight,0.4)&~j.match(mu_tight,0.4)&~j.match(pho_tight,0.4)&j.isgood
            j['isiso'] =  ~(j.match(fj_clean,1.5))&j.isclean.astype(np.bool)
            j['isdcsvL'] = (j.deepcsv>0.1241)&j.isiso.astype(np.bool)
            j['isdflvL'] = (j.deepflv>0.0494)&j.isiso.astype(np.bool)
            j['isdcsvM'] = (j.deepcsv>0.4184)&j.isiso.astype(np.bool)
            j['isdflvM'] = (j.deepflv>0.2770)&j.isiso.astype(np.bool)
            j['isdcsvT'] = (j.deepcsv>0.7527)&j.isiso.astype(np.bool)
            j['isdflvT'] = (j.deepflv>0.7264)&j.isiso.astype(np.bool)

            leading_j = j[j.pt.argmax()]
            leading_j = leading_j[leading_j.isclean.astype(np.bool)]

            j_good = j[j.isgood.astype(np.bool)]
            j_clean = j[j.isclean.astype(np.bool)]
            j_iso = j[j.isiso.astype(np.bool)]
            j_dcsvL = j[j.isdcsvL]
            j_dflvL = j[j.isdflvL]
            j_dcsvM = j[j.isdcsvM]
            j_dflvM = j[j.isdflvM]
            j_dcsvT = j[j.isdcsvT]
            j_dflvT = j[j.isdflvT]
            j_antidcsvL = j[~(j.isdcsvL)]
            j_HEM = j[j.isHEM.astype(np.bool)]

            j_ntot=j.counts
            j_ngood=j_good.counts
            j_nclean=j_clean.counts
            j_niso=j_iso.counts
            j_ndcsvL=j_dcsvL.counts
            j_ndflvL=j_dflvL.counts
            j_ndcsvM=j_dcsvM.counts
            j_ndflvM=j_dflvM.counts
            j_ndcsvT=j_dcsvT.counts
            j_ndflvT=j_dflvT.counts
            j_nantidcsvL=j_antidcsvL.counts
            j_nHEM = j_HEM.counts

            ###
            #Calculating derivatives
            ###
            ele_pairs = e_loose.distincts()
            diele = leading_e
            leading_diele = leading_e
            if ele_pairs.i0.content.size>0:
                diele = ele_pairs.i0+ele_pairs.i1
                leading_diele = diele[diele.pt.argmax()]

            mu_pairs = mu_loose.distincts()
            dimu = leading_mu
            leading_dimu = leading_mu
            if mu_pairs.i0.content.size>0:
                dimu = mu_pairs.i0+mu_pairs.i1
                leading_dimu = dimu[dimu.pt.argmax()]

            observable = {}
            observable["hadronic"] = met
            observable["isoneM"] = met+leading_mu.sum()
            observable["isoneE"] = met+leading_e.sum()
            observable["istwoM"] = met+leading_dimu.sum()
            observable["istwoE"] = met+leading_diele.sum()

            # u={}
            # u["hadronic"] = met
            # u["isoneM"] = met+leading_mu.sum()
            # u["isoneE"] = met+leading_e.sum()
            # u["istwoM"] = met+leading_dimu.sum()
            # u["istwoE"] = met+leading_diele.sum()
            # u["isoneA"] = met+leading_pho.sum()

            lepSys={}
            lepSys["hadronic"] = met
            lepSys["isoneM"] = leading_mu.sum()
            lepSys["isoneE"] = leading_e.sum()
            lepSys["istwoM"] = leading_dimu.sum()
            lepSys["istwoE"] = leading_diele.sum()
            # lepSys["isoneA"] = leading_pho.sum()

            leadlepton={}
            leadlepton["hadronic"] = met
            leadlepton["isoneM"] = leading_mu.sum()
            leadlepton["isoneE"] = leading_e.sum()
            leadlepton["istwoM"] = leading_mu.sum()
            leadlepton["istwoE"] = leading_e.sum()
            # leadlepton["isoneA"] = leading_pho.sum()

            ###
            #Calculating weights
            ###

            ###
            # For MC, retrieve the LHE weights, to take into account NLO destructive interference, and their sum
            ###

            genw = np.ones_like(df['MET_pt'])
            sumw = 1.
            wnlo = np.ones_like(df['MET_pt'])
            adhocw = np.ones_like(df['MET_pt'])
            if self._xsec[dataset] != -1:
                genw = df['genWeight']
                sumw = genw.sum()

                gen_flags = df['GenPart_statusFlags']
                LastCopy = (gen_flags&(1 << 13))==0
                genLastCopy = Initialize({'pt':df['GenPart_pt'][LastCopy],
                                  'eta':df['GenPart_eta'][LastCopy],
                                  'phi':df['GenPart_phi'][LastCopy],
                                  'mass':df['GenPart_mass'][LastCopy],
                                  'pdgid':df['GenPart_pdgId'][LastCopy],
                                  #'status':df['GenPart_status'][LastCopy],
                                  'flags':df['GenPart_statusFlags'][LastCopy],
                                  #'motherid':df['GenPart_genPartIdxMother'][LastCopy]})
                                  })

                #genLastCopy = gen[gen.flags&(1 << 13)==0]
                genTops = genLastCopy[abs(genLastCopy.pdgid)==6]
                genWs = genLastCopy[abs(genLastCopy.pdgid)==24]
                genZs = genLastCopy[abs(genLastCopy.pdgid)==23]
                genAs = genLastCopy[abs(genLastCopy.pdgid)==22]
                genHs = genLastCopy[abs(genLastCopy.pdgid)==25]

                isTT = (genTops.counts==2)
                isW  = (genTops.counts==0)&(genWs.counts==1)&(genZs.counts==0)&(genAs.counts==0)&(genHs.counts==0)
                isZ  = (genTops.counts==0)&(genWs.counts==0)&(genZs.counts==1)&(genAs.counts==0)&(genHs.counts==0)
                isA  = (genTops.counts==0)&(genWs.counts==0)&(genZs.counts==0)&(genAs.counts==1)&(genHs.counts==0)

                if('TTJets' in dataset): wnlo = np.sqrt(get_ttbar_weight(genTops[0].pt.sum()) * get_ttbar_weight(genTops[1].pt.sum()))
                elif('WJets' in dataset):
                    wnlo = get_nlo_weight[self._year]['w'](genWs[0].pt.sum())
                    if self._year != '2016': adhocw = get_adhoc_weight['w'](genWs[0].pt.sum())
                elif('DY' in dataset or 'ZJets' in dataset):
                    wnlo = get_nlo_weight[self._year]['z'](genZs[0].pt.sum())
                    if self._year != '2016': adhocw = get_adhoc_weight['z'](genZs[0].pt.sum())
                elif('GJets' in dataset): wnlo = get_nlo_weight[self._year]['a'](genAs[0].pt.sum())

            ###
            # Calculate PU weight and systematic variations
            ###

            nvtx = df['PV_npvs']
            pu = get_pu_weight[self._year]['cen'](nvtx)
            puUp = get_pu_weight[self._year]['up'](nvtx)
            puDown = get_pu_weight[self._year]['down'](nvtx)

            ###
            #Importing the MET filters per year from metfilters.py and constructing the filter boolean
            ###

            met_filters = {}
            for flag in met_filter_flags[self._year]:
                if flag in df:
                    met_filters[flag] = df[flag]

            ###
            #Importing the trigger paths per year from trigger.py and constructing the trigger boolean
            ###

            pass_trig = {}
            met_trigger = {}
            for path in met_trigger_paths[self._year]:
                if path in df:
                    met_trigger[path] = df[path]
            passMetTrig = np.zeros_like(df['MET_pt'], dtype=np.bool)
            for path in met_trigger:
                passMetTrig |= met_trigger[path]

            singleele_trigger = {}
            for path in singleele_trigger_paths[self._year]:
                if path in df:
                    singleele_trigger[path] = df[path]
            passSingleEleTrig = np.zeros_like(df['MET_pt'], dtype=np.bool)
            for path in singleele_trigger:
                passSingleEleTrig |= singleele_trigger[path]

            singlepho_trigger = {}
            for path in singlepho_trigger_paths[self._year]:
                if path in df:
                    singlepho_trigger[path] = df[path]
            passSinglePhoTrig = np.zeros_like(df['MET_pt'], dtype=np.bool)
            for path in singlepho_trigger:
                passSinglePhoTrig |= singlepho_trigger[path]

            pass_trig['hadronic'] = passMetTrig
            pass_trig['isoneM'] = passMetTrig
            pass_trig['istwoM'] = passMetTrig
            pass_trig['isoneE'] = passSingleEleTrig
            pass_trig['istwoE'] = passSingleEleTrig
            # pass_trig['isoneA'] =passSinglePhoTrig

            ###
            # Trigger efficiency weight
            ###

            trig = {}
            trig['hadronic'] = get_met_trig_weight[self._year](observable["hadronic"].pt)
            trig['isoneM'] = get_met_trig_weight[self._year](observable["isoneM"].pt)
            trig['istwoM'] = get_met_zmm_trig_weight[self._year](observable["istwoM"].pt)
            trig['isoneE'] = get_ele_trig_weight[self._year](leading_e.eta.sum(), leading_e.pt.sum())
            trig['istwoE'] = trig['isoneE']
            # if ele_pairs.i0.content.size>0:
            #     eff1 = get_ele_trig_weight[self._year](ele_pairs[diele.pt.argmax()].i0.eta.sum(),ele_pairs[diele.pt.argmax()].i0.pt.sum())
            #     eff2 = get_ele_trig_weight[self._year](ele_pairs[diele.pt.argmax()].i1.eta.sum(),ele_pairs[diele.pt.argmax()].i1.pt.sum())
            #     trig['istwoE'] = 1 - (1-eff1)*(1-eff2)
            # trig['isoneA'] = get_pho_trig_weight[self._year](leading_pho.pt.sum())

            ###
            #Event selection
            ###

            selections = processor.PackedSelection()

            selections.add('hadronic', (passMetTrig) & (fj_nclean>0))
            selections.add('isoneM', (j_nclean>0))
            selections.add('istwoM', (j_nclean>0))
            selections.add('isoneE', (passSingleEleTrig) & (j_nclean>0))
            selections.add('istwoE', (passSingleEleTrig) & (j_nclean>0))

            # selections.add('istwoM', (e_nloose==0) & (mu_ntight>=1) & (mu_nloose==2) & (tau_nloose==0)&(pho_nloose==0)&(leading_dimu.mass.sum()>60) & (leading_dimu.mass.sum()<120))
            # selections.add('istwoE', (e_ntight>=1) & (e_nloose==2)&(mu_nloose==0)&(tau_nloose==0)&(pho_nloose==0)&(leading_diele.mass.sum()>60)&(leading_diele.mass.sum()<120))
            # selections.add('isoneA', (e_nloose==0)&(mu_nloose==0)&(tau_nloose==0)&(pho_ntight==1))
            # selections.add('topveto', (leading_fj.TopTagger.sum()<0.25))
            # selections.add('noextrab', (j_ndflvL==0))
            # selections.add('extrab', (j_ndflvL>0))
            # selections.add('ismonohs', (leading_fj.DarkHiggsTagger.sum()>0.2))
            # selections.add('ismonoV', ~(leading_fj.DarkHiggsTagger.sum()>0.2)&(leading_fj.VvsQCDTagger.sum()>0.8))
            # selections.add('ismonojet', ~(leading_fj.DarkHiggsTagger.sum()>0.2)&~(leading_fj.VvsQCDTagger.sum()>0.8))
            # selections.add('mass0', (leading_fj.msd.sum()>40)&(leading_fj.msd.sum()<=60))
            # selections.add('mass1', (leading_fj.msd.sum()>60)&(leading_fj.msd.sum()<=120))
            # selections.add('mass2', (leading_fj.msd.sum()>120)&(leading_fj.msd.sum()<=250))
            # selections.add('noHEMj', (j_nHEM==0))

            # selections.add('istwoM', (e_nloose==0) & (mu_ntight==1) & (mu_nloose==2) & (tau_nloose==0)&(pho_nloose==0)&(leading_dimu.mass.sum()>60) & (leading_dimu.mass.sum()<120))
            # selections.add('istwoE', (e_ntight==1)&(e_nloose==2)&(mu_nloose==0)&(tau_nloose==0)&(pho_nloose==0)&(leading_diele.mass.sum()>60)&(leading_diele.mass.sum()<120))

            ###
            #Adding weights and selections
            ###

            weights = {}
            regions = {}
            for k in selected_regions[dataset]:
                weights[k] = processor.Weights(df.size)
                weights[k].add('nlo',wnlo)
                weights[k].add('adhoc',adhocw)
                weights[k].add('genw',genw)
                weights[k].add('pileup',pu,puUp,puDown)
                weights[k].add('passMetFilters',np.prod([met_filters[key] for key in met_filters], axis=0))
                weights[k].add('trig', trig[k])
                weights[k].add('pass_trig', pass_trig[k])

                if (k=="hadronic"):
                    selections.add(k+'signal',   (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) &(fj_nclean==1) & (j_ndflvM==0) & (mu_nloose==0) & (e_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                    selections.add(k+'ttbar',    (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) & (fj_nclean==1) & (j_ndflvM==1) & (mu_nloose==0) & (e_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                    selections.add(k+'ttbar_mu', (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) & (fj_nclean==1) & (j_ndflvM==1) & (mu_ntight==1) & (mu_nloose==1) & (e_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                    selections.add(k+'ttbar_e',  (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) & (fj_nclean==1) & (j_ndflvM==1) & (mu_nloose==0) & (e_ntight==1) & (e_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                    selections.add(k+'wjets_mu', (observable[k].pt.sum()>250) & (fj_nclean==1) & (j_ndflvM==0) & (mu_ntight==1) & (mu_nloose==1) & (e_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                    selections.add(k+'wjets_e',  (observable[k].pt.sum()>250) & (fj_nclean==1) & (j_ndflvM==0) & (e_ntight==1) & (e_nloose==1) & (mu_nloose==0) & (pho_nloose==0) & (tau_nloose==0))
                if (k=="isoneM"):
                    selections.add(k+'signal', (met.pt.sum()>150) & (j_ndflvM==1) & (mu_ntight==1) & (mu_nloose==1) & (e_nloose==0) & (pho_nloose==0))
                    selections.add(k+'ttbar',  (met.pt.sum()>150) & (j_ndflvM>=2) & (mu_ntight==1) & (mu_nloose==1) & (e_nloose==0) & (pho_nloose==0))
                    selections.add(k+'wjets',  (met.pt.sum()>150) & (j_ndflvM==0) & (mu_ntight==1) & (mu_nloose==1) & (e_nloose==0) & (pho_nloose==0))
                if (k=="istwoM"):
                    selections.add(k+'zjets', (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) & (fj_nclean==1) & (mu_ntight==1) & (mu_nloose==2) & (e_nloose==0) & (leading_dimu.mass.sum()>60) & (leading_dimu.mass.sum()<120) & (pho_nloose==0) & (tau_nloose==0))
                if (k=="isoneE"):
                    selections.add(k+'signal', (met.pt.sum()>150) & (j_ndflvM==1) & (e_ntight==1) & (e_nloose==1) & (mu_nloose==0) & (pho_nloose==0))
                    selections.add(k+'ttbar',  (met.pt.sum()>150) & (j_ndflvM>=2) & (e_ntight==1) & (e_nloose==1) & (mu_nloose==0) & (pho_nloose==0))
                    selections.add(k+'wjets',  (met.pt.sum()>150) & (j_ndflvM==0) & (e_ntight==1) & (e_nloose==1) & (mu_nloose==0) & (pho_nloose==0))
                if (k=="istwoE"):
                    selections.add(k+'zjets',  (observable[k].pt.sum()>250) & (leading_fj.pt.sum()>250) & (fj_nclean==1) & (mu_nloose==0) & (e_ntight==1) & (e_nloose==2) & (leading_diele.mass.sum()>60) & (leading_diele.mass.sum()<120) & (pho_nloose==0) & (tau_nloose==0))

                if (k=="hadronic"):
                    regions[k+'_signal'] = {k,k+'signal'}
                    regions[k+'_ttbar'] = {k,k+'ttbar'}
                    regions[k+'_ttbar_mu'] = {k,k+'ttbar_mu'}
                    regions[k+'_ttbar_e'] = {k,k+'ttbar_e'}
                    regions[k+'_wjets_mu'] = {k,k+'wjets_mu'}
                    regions[k+'_wjets_e'] = {k,k+'wjets_e'}
                if (k=="isoneM" or k=="isoneE"):
                    regions[k+'_signal'] = {k,k+'signal'}
                    regions[k+'_ttbar'] = {k,k+'ttbar'}
                    regions[k+'_wjets'] = {k,k+'wjets'}
                if (k=="istwoM" or k=="istwoE"): regions[k+'_zjets'] = {k,k+'zjets'}

            variables = {}
            variables['j1pt'] = leading_j.pt
            variables['j1eta'] = leading_j.eta
            variables['j1phi'] = leading_j.phi
            variables['fj1pt'] = leading_fj.pt
            variables['fj1eta'] = leading_fj.eta
            variables['fj1phi'] = leading_fj.phi
            variables['e1pt'] = leading_e.pt
            variables['e1phi'] = leading_e.phi
            variables['e1eta'] = leading_e.eta
            variables['dielemass'] = leading_diele.mass
            variables['mu1pt'] = leading_mu.pt
            variables['mu1phi'] = leading_mu.phi
            variables['mu1eta'] = leading_mu.eta
            variables['dimumass'] = leading_dimu.mass
            variables['njets'] = j_nclean
            variables['ndcsvL'] = j_ndcsvL
            variables['ndflvL'] = j_ndflvL
            variables['ndcsvM'] = j_ndcsvM
            variables['ndflvM'] = j_ndflvM
            variables['ndcsvT'] = j_ndcsvT
            variables['ndflvT'] = j_ndflvT
            variables['nantidcsvL'] = j_nantidcsvL
            variables['nfjtot'] = fj_ntot
            variables['nfjgood'] = fj_ngood
            variables['nfjclean'] = fj_nclean
            variables['fjmass'] = leading_fj.mass
            variables['TopTagger'] = leading_fj.TopTagger
            variables['DarkHiggsTagger'] = leading_fj.DarkHiggsTagger
            variables['VvsQCDTagger'] = leading_fj.VvsQCDTagger
            variables['probTbcq']      = leading_fj.probTbcq
            variables['probTbqq']      = leading_fj.probTbqq
            variables['probTbc']       = leading_fj.probTbc
            variables['probTbq']       = leading_fj.probTbq
            variables['probWcq']       = leading_fj.probWcq
            variables['probWqq']       = leading_fj.probWqq
            variables['probZbb']       = leading_fj.probZbb
            variables['probZcc']       = leading_fj.probZcc
            variables['probZqq']       = leading_fj.probZqq
            variables['probHbb']       = leading_fj.probHbb
            variables['probHcc']       = leading_fj.probHcc
            variables['probHqqqq']     = leading_fj.probHqqqq
            variables['probQCDbb']     = leading_fj.probQCDbb
            variables['probQCDcc']     = leading_fj.probQCDcc
            variables['probQCDb']      = leading_fj.probQCDb
            variables['probQCDc']      = leading_fj.probQCDc
            variables['probQCDothers'] = leading_fj.probQCDothers

            hout = self.accumulator.identity()
            hout['sumw'].fill(dataset=dataset, sumw=1, weight=sumw)
            i = 0
            while i < len(selected_regions[dataset]):
                r = selected_regions[dataset][i]
                weight = weights[r].weight()
                for s in ["signal","ttbar","ttbar_mu","ttbar_e","wjets","wjets_e","wjets_mu","zjets"]:
                    if (r+'_'+s not in regions): continue
                    cut = selections.all(*regions[r+'_'+s])
                    flat_variables = {k: v[cut].flatten() for k, v in variables.items()}
                    flat_weights = {k: (~np.isnan(v[cut])*weight[cut]).flatten() for k, v in variables.items()}
                    for histname, h in hout.items():
                        if not isinstance(h, hist.Hist):
                            continue
                        elif histname == 'sumw':
                            continue
                        elif histname == 'recoil':
                            h.fill(dataset=dataset, category=r, control_region=s, recoil=observable[r].pt, weight=weight*cut)
                        elif histname == 'CaloMinusPfOverRecoil':
                            h.fill(dataset=dataset, category=r, control_region=s, CaloMinusPfOverRecoil= abs(calomet.pt - met.pt) / observable[r].pt, weight=weight*cut)
                        elif histname == 'mindphi':
                            h.fill(dataset=dataset, category=r, control_region=s, mindphi=abs(observable[r].delta_phi(j_clean)).min(), weight=weight*cut)
                        elif histname == 'diledphi':
                            h.fill(dataset=dataset, category=r, control_region=s, diledphi=abs(lepSys[r].delta_phi(j_clean)).min(), weight=weight*cut)
                        elif histname == 'ledphi':
                            h.fill(dataset=dataset, category=r, control_region=s, ledphi=abs(leadlepton[r].delta_phi(j_clean)).min(), weight=weight*cut)
                        elif histname == 'recoilVSmindphi':
                            h.fill(dataset=dataset, category=r, control_region=s, recoil=observable[r].pt, mindphi=abs(observable[r].delta_phi(j_clean)).min(), weight=weight*cut)
                        elif histname == 'mu1drj':
                            if r == 'isoneM' or r == 'istwoM':
                                h.fill(dataset=dataset, category=r, control_region=s, mu1drj=leadlepton[r].delta_r(j_clean).min(), weight=weight*cut)
                        elif histname == 'e1drj':
                            if r == 'isoneE' or r == 'istwoE' :
                                h.fill(dataset=dataset, category=r, control_region=s, e1drj=leadlepton[r].delta_r(j_clean).min(), weight=weight*cut)
                        else:
                            flat_variable = {histname: flat_variables[histname]}
                            h.fill(dataset=dataset, category=r, control_region=s, **flat_variable, weight=flat_weights[histname])
                i += 1
            return hout

    def postprocess(self, accumulator):
            scale = {}
            for d in accumulator['sumw'].identifiers('dataset'):
                dataset = d.name
                if self._xsec[dataset]!= -1: scale[dataset] = self._lumi*self._xsec[dataset]
                else: scale[dataset] = 1

            for histname, h in accumulator.items():
                if histname == 'sumw': continue
                if isinstance(h, hist.Hist):
                    h.scale(scale, axis="dataset")

            return accumulator

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-y', '--year', help='year', dest='year')
    parser.add_option('-l', '--lumi', help='lumi', dest='lumi', type=float)
    (options, args) = parser.parse_args()

    lumis = {} #Values from https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmVAnalysisSummaryTable
    lumis['2016']=35.92
    lumis['2017']=41.53
    lumis['2018']=59.97
    lumi = 1000.*float(lumis[options.year])
    if options.lumi: lumi=1000.*options.lumi

    with open('metadata/'+options.year+'.json') as fin:
        samplefiles = json.load(fin)
        xsec = {k: v['xs'] for k,v in samplefiles.items()}

    corrections = load('secondary_inputs/corrections.coffea')
    triggers    = load('secondary_inputs/triggers.coffea')
    ids         = load('secondary_inputs/ids.coffea')
    metfilters  = load('secondary_inputs/metfilters.coffea')

    columns = """
    MET_pt
    MET_phi
    CaloMET_pt
    CaloMET_phi
    Electron_pt
    Electron_eta
    Electron_phi
    Electron_mass
    Muon_pt
    Muon_eta
    Muon_phi
    Muon_mass
    Tau_pt
    Tau_eta
    Tau_phi
    Tau_mass
    Photon_pt
    Photon_eta
    Photon_phi
    Photon_mass
    AK15Puppi_pt
    AK15Puppi_eta
    AK15Puppi_phi
    AK15Puppi_mass
    Jet_pt
    Jet_eta
    Jet_phi
    Jet_mass
    Jet_btagDeepB
    Jet_btagDeepFlavB
    GenPart_pt
    GenPart_eta
    GenPart_phi
    GenPart_mass
    GenPart_pdgId
    GenPart_status
    GenPart_statusFlags
    GenPart_genPartIdxMother
    PV_npvs
    Electron_cutBased
    Electron_dxy
    Electron_dz
    Muon_pfRelIso04_all
    Muon_tightId
    Muon_mediumId
    Muon_dxy
    Muon_dz
    Tau_idMVAoldDM2017v2
    Tau_idDecayMode
    Photon_cutBased
    Photon_electronVeto
    Photon_cutBasedBitmap
    AK15Puppi_jetId
    Jet_jetId
    Jet_neHEF
    Jet_neEmEF
    Jet_chHEF
    Jet_chEmEF
    AK15Puppi_probTbcq
    AK15Puppi_probTbqq
    AK15Puppi_probTbc
    AK15Puppi_probTbq
    AK15Puppi_probWcq
    AK15Puppi_probWqq
    AK15Puppi_probZbb
    AK15Puppi_probZcc
    AK15Puppi_probZqq
    AK15Puppi_probHbb
    AK15Puppi_probHcc
    AK15Puppi_probHqqqq
    AK15Puppi_probQCDbb
    AK15Puppi_probQCDcc
    AK15Puppi_probQCDb
    AK15Puppi_probQCDc
    AK15Puppi_probQCDothers
    """.split()

    processor_instance=AnalysisProcessor(columns=columns,
                                         year=options.year,
                                         xsec=xsec,
                                         lumi=lumi,
                                         corrections=corrections,
                                         triggers=triggers,
                                         ids=ids,
                                         metfilters=metfilters)

    save(processor_instance, 'processors/monotop'+options.year+'.coffea')
