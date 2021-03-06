import FWCore.ParameterSet.Config as cms

#Process name:
process = cms.Process("SingleTop")

#MessageLogger options:
process.load("FWCore.MessageLogger.MessageLogger_cfi")

process.options = cms.untracked.PSet(
    wantSummary = cms.untracked.bool(True),
    FailPath = cms.untracked.vstring('ProductNotFound','Type Mismatch')
    )

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(200) )
#process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

ChannelName = "Mu_A13Jul"


#Input file:
process.source = cms.Source (
    "PoolSource",
    fileNames = cms.untracked.vstring (
#    "file:/afs/cern.ch/work/o/oiorio/public/xFrancescoFab/T_t-channel_Synch.root"
    "file:/afs/cern.ch/work/o/oiorio/public/xFrancescoFab/DataReRecoA.root"
    ),
    duplicateCheckMode = cms.untracked.string('noDuplicateCheck')
)

process.MessageLogger.cerr.FwkReport.reportEvery = 10

#Data or MC:
isData = True

#Gsf electron or PF electron:
doGsfElectrons = False

#Add nJ >= 2 cut:
addJetsCut = True 

#Geometry:
process.load("Configuration.Geometry.GeometryIdeal_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.load("Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff") ### real data

#Tag:
#process.GlobalTag.globaltag = cms.string('START53_V7G::All')
process.GlobalTag.globaltag = cms.string('FT_53_V6C_AN3::All')

# dummy output: needed to avoid crash
process.out = cms.OutputModule(
    "PoolOutputModule",
    fileName = cms.untracked.string('dummy.root'),
    outputCommands = cms.untracked.vstring(""),
)

# ---> PAT + Single top sequences <---
process.load("PhysicsTools.PatAlgos.patSequences_cff") 

process.goodOfflinePrimaryVertices = cms.EDFilter( "PrimaryVertexObjectFilter" ,
                                                   filterParams = cms.PSet( minNdof = cms.double( 4. ) , maxZ = cms.double( 24. ) , maxRho = cms.double( 2. ) ) ,
                                                   filter = cms.bool( True) , src = cms.InputTag( 'offlinePrimaryVertices' ) )

# Configure PAT to use PFBRECO instead of AOD sources
# this function will modify the PAT sequences.
from PhysicsTools.PatAlgos.tools.pfTools import *
from PhysicsTools.PatAlgos.tools.trigTools import *
from PhysicsTools.PatUtils.tools.metUncertaintyTools import *

postfix = ""
runOnMC = not(isData)
jetAlgoName = "AK5"

if runOnMC:#MC
    jetCorrections=['L1FastJet','L2Relative','L3Absolute']
else:#Data
    jetCorrections=['L1FastJet','L2Relative','L3Absolute','L2L3Residual']

############ PRINTOUT ###################
sep_line = "-" * 50
print sep_line
print 'running the following PFBRECO sequence:'
print jetAlgoName
print 'run on MC        : ', runOnMC
print sep_line
print 'postfix       : ', postfix
print sep_line
print 'JEC        : ', jetCorrections
print sep_line
#########################################

usePF2PAT(process, runPF2PAT=True, jetAlgo=jetAlgoName, runOnMC=runOnMC, postfix=postfix,
          jetCorrections=('AK5PFchs',jetCorrections), pvCollection=cms.InputTag('goodOfflinePrimaryVertices'),
          typeIMetCorrections=isData)

if (not(isData)):
    from PhysicsTools.PatUtils.tools.metUncertaintyTools import runMEtUncertainties
    runMEtUncertainties(process,electronCollection = "selectedPatElectrons", doSmearJets= False, muonCollection = "selectedPatMuons", tauCollection="selectedPatTaus", jetCollection = "selectedPatJets")
#Note: we run the MET uncertainty tools if it is MC. If it is data, the type 1 corrected METs

# CONFIGURE LEPTONS for the analysis

# Use DR = 0.3 for PF electrons:
process.pfIsolatedElectrons.isolationValueMapsCharged = cms.VInputTag(cms.InputTag("elPFIsoValueCharged03PFId"))
process.pfIsolatedElectrons.deltaBetaIsolationValueMap = cms.InputTag("elPFIsoValuePU03PFId")
process.pfIsolatedElectrons.isolationValueMapsNeutral = cms.VInputTag(cms.InputTag("elPFIsoValueNeutral03PFId"), cms.InputTag("elPFIsoValueGamma03PFId"))

if doGsfElectrons:
    # Gsf Electrons
    # Use DR = 0.3:
    useGsfElectrons(process,postfix,"03")
if not(doGsfElectrons):
    # Set Isolation for PAT Electrons
    process.patElectrons.isolationValues = cms.PSet( pfChargedHadrons = cms.InputTag("elPFIsoValueCharged03PFId"), pfChargedAll = cms.InputTag("elPFIsoValueChargedAll03PFId"), pfPUChargedHadrons = cms.InputTag("elPFIsoValuePU03PFId"), pfNeutralHadrons = cms.InputTag("elPFIsoValueNeutral03PFId"), pfPhotons = cms.InputTag("elPFIsoValueGamma03PFId") )

#Apply PFnoPU:
process.pfPileUp.Enable = True
process.pfPileUp.checkClosestZVertex = cms.bool(False)


# Prepare MVA electronId
process.load("EGamma.EGammaAnalysisTools.electronIdMVAProducer_cfi")
process.mvaID = cms.Sequence(  process.mvaTrigV0 + process.mvaNonTrigV0 )
process.patElectronIDs = cms.Sequence( process.mvaID )
# Add MVA electronId
process.electronIDSources = cms.PSet(
    mvaTrigV0    = cms.InputTag("mvaTrigV0"),
    mvaNonTrigV0    = cms.InputTag("mvaNonTrigV0")
    )

process.patElectrons.electronIDSources = process.electronIDSources

# PAT Muons
# No special cfg for PAT muons

# Define the PAT sequence:
process.patseq = cms.Sequence(
    process.goodOfflinePrimaryVertices *
    process.patElectronIDs *
    getattr(process,"patPF2PATSequence"+postfix)
    )

# Add PUJetID
process.load("CMGTools.External.pujetidsequence_cff")

# Define new PAT muons/electrons with no isolation in pf reco (ZeroIso suffix)
# They will be used to get anti-isolated leptons:

# MuonsZeroIso
process.pfIsolatedMuonsZeroIso = process.pfIsolatedMuons.clone(combinedIsolationCut =  cms.double(float("inf")),
                                                               isolationCut =  cms.double(float("inf"))
                                                               )
from tH.SingleTop.AdaptPFMuonsFix_cff import adaptPFMuonsAnd
process.patMuonsZeroIso = process.patMuons.clone(pfMuonSource = cms.InputTag("pfIsolatedMuonsZeroIso"))
# use pf isolation, but do not change matching:
tmp = process.muonMatch.src

adaptPFMuonsAnd(process, process.patMuonsZeroIso, "")
process.muonMatch.src = tmp
process.muonMatchZeroIso = process.muonMatch.clone(src = cms.InputTag("pfIsolatedMuonsZeroIso"))
process.patMuonsZeroIso.genParticleMatch = cms.InputTag("muonMatchZeroIso")
process.patMuonsZeroIso.pfMuonSource = cms.InputTag("pfIsolatedMuonsZeroIso")


# ElectronsZeroIso
process.pfIsolatedElectronsZeroIso = process.pfIsolatedElectrons.clone(combinedIsolationCut = cms.double(float("inf")),
                                                                       isolationCut =  cms.double(float("inf")),
                                                                       )
process.patElectronsZeroIso = process.patElectrons.clone(pfElectronSource = cms.InputTag("pfIsolatedElectronsZeroIso"))

#Define ZeroIso leptons sequence:
if isData:
    process.ZeroIsoLeptonSequence = cms.Sequence(
        process.pfIsolatedMuonsZeroIso +
        process.patMuonsZeroIso +
        process.pfIsolatedElectronsZeroIso +
        process.patElectronsZeroIso
        )
else:    
    process.ZeroIsoLeptonSequence = cms.Sequence(
        process.pfIsolatedMuonsZeroIso +
        process.muonMatchZeroIso +
        process.patMuonsZeroIso +
        process.pfIsolatedElectronsZeroIso +
        process.patElectronsZeroIso
        )
    
##### Define leptons collections useful in single top analysis

# Veto leptons
process.load("tH.SingleTop.userDataLeptonProducers_cfi") 

process.vetoMuons = process.userDataMuons.clone(
    cut = cms.string(" (isGlobalMuon || isTrackerMuon) " +
                     "& pt > 10 & abs(eta) < 2.5 " +
                     "& userFloat(\"DeltaCorrectedIso\") <0.2 ")
)

process.vetoElectrons = process.userDataElectrons.clone(
    cut = cms.string("ecalDrivenMomentum.pt > 20 " +
                     "& abs(eta) < 2.5 " +
                     "& userFloat(\"RhoCorrectedIso\") <0.15" +
                     "& userFloat(\"PassesVetoID\") >0.0")
)

process.vetoElectronsMVA = process.userDataElectrons.clone(
    cut =  cms.string(" ecalDrivenMomentum.pt > 20" +
                      "& abs(eta) < 2.5 && userFloat(\"RhoCorrectedIso\") <0.15" +
                      "& electronID('mvaTrigV0') >0.0")
)

# Tight leptons
process.tightMuons = process.userDataMuons.clone(
    cut = cms.string(" pt > 26 & isGlobalMuon && isPFMuon & abs(eta) < 2.1 && normChi2 < 10 && track.hitPattern.trackerLayersWithMeasurement>5 "+
                     "& numberOfMatchedStations() > 1 && innerTrack.hitPattern.numberOfValidPixelHits > 0 " +
                     "& globalTrack.hitPattern.numberOfValidMuonHits > 0" +
                     "& userFloat('VertexDxy')<0.02" +
                     "& userFloat('VertexDz')<0.5" +
                     "& userFloat(\"DeltaCorrectedIso\") <0.12 " )
)

process.tightElectrons = process.userDataElectrons.clone(
    cut =  cms.string(" ecalDrivenMomentum.pt > 30  && abs(eta)<2.5" +
                      "& ( abs(superCluster.eta)> 1.5660 || abs(superCluster.eta)<1.4442)" +
                      "& gsfTrack.trackerExpectedHitsInner.numberOfHits <=0" +
                      "& passConversionVeto" +
                      "& userFloat('VertexDxy')<0.02" +
                      "& userFloat('RhoCorrectedIso')<0.1" )
)

# Tight leptons ZeroIso
process.tightMuonsZeroIso = process.userDataMuons.clone(
    src = cms.InputTag("patMuonsZeroIso"),
    cut = cms.string(" pt > 26 & isGlobalMuon && isPFMuon & abs(eta) < 2.1 && normChi2 < 10 && track.hitPattern.trackerLayersWithMeasurement>5 "+
                     "& numberOfMatchedStations() > 1 && innerTrack.hitPattern.numberOfValidPixelHits > 0 " +
                     "& globalTrack.hitPattern.numberOfValidMuonHits > 0")
)

process.tightElectronsZeroIso = process.userDataElectrons.clone(
    src = cms.InputTag("patElectronsZeroIso"),
    cut =  cms.string(" ecalDrivenMomentum.pt > 30  && abs(eta)<2.5" +
                      "& ( abs(superCluster.eta)> 1.5660 || abs(superCluster.eta)<1.4442)" +
                      "& passConversionVeto")
)

##### Filtering on leptons numbers
process.load("tH.SingleTop.leptonCounterFilter_cfi") 
# Select events with at least 1 tight lepton OR at least one tight leptonNoIso
process.countLeptons.minNumberLoose = 0
process.countLeptons.maxNumberLoose = 99
process.countLeptons.minNumberTight = 1
process.countLeptons.maxNumberTight = 99
process.countLeptons.minNumberQCD = 1
process.countLeptons.maxNumberQCD = 99

# define Jets for single top analysis
process.load("tH.SingleTop.userDataJetsProducer_cfi") 

process.load("tH.SingleTop.userDataMETsProducer_cfi") 

#definition: Jets Loose
process.topJetsPF.cut = cms.string("numberOfDaughters()>1 & pt()> 20 && abs(eta())<5 " +
                                   " & ((abs(eta())>=2.4) || ( chargedHadronEnergyFraction() > 0 & chargedMultiplicity()>0 " +
                                   " & chargedEmEnergyFraction()<0.99))" +
                                   " & neutralEmEnergyFraction() < 0.99 & neutralHadronEnergyFraction() < 0.99 ")

process.topJetsPF.isData = isData
process.topMETsPF.isData = isData
if isData: 
    process.topMETsPF.metsSrc = cms.InputTag("patMETs")

process.basePath = cms.Sequence(
    process.vetoMuons +
    process.vetoElectrons +
    process.vetoElectronsMVA +
    process.topJetsPF +
    process.topMETsPF +
    process.tightMuonsZeroIso +
    process.tightElectronsZeroIso +
    process.tightMuons +
    process.tightElectrons
)

#Trigger filter to be eventually used:
import HLTrigger.HLTfilters.triggerResultsFilter_cfi as triggerFilter

process.HLTFilterMu2012  = triggerFilter.triggerResultsFilter.clone(
    hltResults = cms.InputTag( "TriggerResults","","HLT" ),
    triggerConditions = ["HLT_*"],#All trigger paths are included in the skim
#   triggerConditions = ["HLT_IsoMu24_eta2p1_v*"],
#   triggerConditions = ["HLT_Ele27_WP80_v*"],
    l1tResults = '',
    throw = False
    )

from PhysicsTools.PatAlgos.selectionLayer1.jetCountFilter_cfi import *
process.jetsCut = countPatJets.clone(src = 'topJetsPF', minNumber = 2)

# Overall skim path
process.singleTopSkimPath = cms.Path(
    process.HLTFilterMu2012 *
    process.patseq +
    process.puJetIdSqeuence +
    process.puJetIdSqeuenceChs *
    process.ZeroIsoLeptonSequence *
    process.basePath #+
# moved preselection in a standalone path
#    process.preselection# + 
#    process.nTuplesSkim 
    )

# Load recommended event filters
process.load("tH.SingleTop.SingleTopEventFilters_cff") 

# Define event filtering path
#process.preselection = cms.Sequence(
process.preselection = cms.Path(
    process.HLTFilterMu2012 *
    process.HBHENoiseFilter *
    process.scrapingVeto *
    process.CSCTightHaloFilter *
    process.hcalLaserEventFilter *
    process.EcalDeadCellTriggerPrimitiveFilter *
    process.EcalDeadCellBoundaryEnergyFilter *
    process.goodVertices *
    process.trackingFailureFilter *
    process.eeBadScFilter *
    process.ecalLaserCorrFilter *
    ~process.manystripclus53X *
    ~process.toomanystripclus53X *
    ~process.logErrorTooManyClusters *
    process.countLeptons
    )

if addJetsCut:
    process.preselection += process.jetsCut

process.fullPath = cms.Schedule(
    process.singleTopSkimPath,
    process.preselection
    )

#Objects included in the pat-tuples
savePatTupleSkimLoose = cms.untracked.vstring(
    'drop *',
    'keep patMuons_selectedPatMuons_*_*',
    'keep patElectrons_selectedPatElectrons_*_*',
    'keep patJets_selectedPatJets_*_*',
    'keep *_selectedPatJets_genJets_*', # to get embedded genJets
    'keep patMETs_patMETs_*_*',
    'keep *_kt6PFJets_rho_*',
    'keep *_topJetsPF_*_*',
    'keep *_topMETsPF_*_*',
    'keep patMuons_vetoMuons_*_*',
    'keep *_vetoElectrons_*_*',
    'keep *_vetoElectronsMVA_*_*',
    'keep patMuons_tightMuons_*_*',
    'keep *_tightElectrons_*_*',
    'keep *_tightElectronsZeroIso_*_*',
    'keep *_tightMuonsZeroIso_*_*',
# vertex
    'keep *_offlineBeamSpot_*_*',
    'keep *_offlinePrimaryVertices_*_*',
    'keep *_goodOfflinePrimaryVertices_*_*', # needed by SingleTopVertexInfoDumper module
# Trigger results
    "keep *_TriggerResults_*_*",
# gen particles
    'keep *_genParticles_*_*',
# gen info
    'keep PileupSummaryInfos_*_*_*',
    'keep GenEventInfoProduct_*_*_*',
    'keep GenRunInfoProduct_*_*_*',
    'keep LHEEventProduct_*_*_*',
    'keep *_genEventScale_*_*',
    'keep *_PDFInfo_*_*',
)


process.singleTopPatTuple = cms.OutputModule(
    "PoolOutputModule",
    fileName = cms.untracked.string('singleTopSkim_'+ChannelName+'.root'),
    SelectEvents   = cms.untracked.PSet(
      SelectEvents = cms.vstring(
        'preselection')
#        'pathSelection')
      ),
    outputCommands = savePatTupleSkimLoose
    )
process.singleTopPatTuple.dropMetaData = cms.untracked.string("DROPPED")


#### Ntuplization step ###
########################################################
process.load("PhysicsTools.HepMCCandAlgos.flavorHistoryPaths_cfi")
########################################################

######### GET generator info ##############
#genJets:
process.genJetsPF = cms.EDProducer(
    "SingleTopGenJetPtEtaProducer",
    jetsSource = cms.InputTag("topJetsPF"),
)
#genAllJets:
process.genAllJetsPF = cms.EDProducer(
    "SingleTopGenJetPtEtaProducer",
    jetsSource = cms.InputTag("selectedPatJets"),
)
#PU Info
process.NVertices = cms.EDProducer("SingleTopPileUpProducer")

#n gen particles Info
process.NGenParticles = cms.EDProducer("SingleTopNGenParticlesProducer")

#PDF Info
process.PDFInfo = cms.EDProducer( "PDFInfoDumper" )

#Part of MC Truth particles production
process.MCTruthParticles = cms.EDProducer(
    "SingleTopMCProducer",
    genParticlesSource = cms.InputTag("genParticles")
)
#############################################

######### EdmNtuples production ##############
process.load("tH.SingleTop.SingleTopNtuplizers_cff")

# Ntuple sequence
process.genPath = cms.Sequence(
    process.genJetsPF +
    process.genAllJetsPF +
    process.NVertices +
    process.NGenParticles +
    process.PDFInfo           
)

process.singleTopNtuplePath = cms.Sequence(
    process.nTuplesSkim 
)

process.singleTopSkimPath += process.singleTopNtuplePath
if not(isData): process.singleTopSkimPath += process.genPath

from tH.SingleTop.SingleTopNtuplizers_cff import saveNTuplesSkimLoose

#Add MC Truth information:
doMCTruth = True
if isData:
    doMCTruth = False

if doMCTruth:
    process.MCTruth = cms.Sequence(
        process.MCTruthParticles +
        process.nTuplesSkimMCTruth
    )
    process.singleTopSkimPath += process.MCTruth

    saveNTuplesSkimLoose.append('keep  floats_MCTruthParticles_*_*')
    saveNTuplesSkimLoose.append('keep  ints_MCTruthParticles_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCLeptons_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCQuarks_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCNeutrinos_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCBQuarks_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTops_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsW_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsBQuark_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsLepton_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsNeutrino_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsQuark_*_*')
    saveNTuplesSkimLoose.append('keep  floats_singleTopMCTopsQuarkBar_*_*')
                                                            

## Output module configuration
process.singleTopNTupleOut = cms.OutputModule(
    "PoolOutputModule",
    fileName = cms.untracked.string('singleTopEdmNtuple_'+ChannelName+'.root'),
    SelectEvents   = cms.untracked.PSet( SelectEvents = cms.vstring('preselection')),
    outputCommands = saveNTuplesSkimLoose,
    )

process.singleTopNTupleOut.dropMetaData = cms.untracked.string("ALL")

process.outpath = cms.EndPath(
    process.singleTopPatTuple +
    process.singleTopNTupleOut
    )

