import FWCore.ParameterSet.Config as cms

process = cms.Process("NTPFILT")

#### Simple cfg to apply event filter to ntuple
#### It just apply a filter on HLT trigger paths, but other filters can be added here

process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )
process.source = cms.Source("PoolSource")

### Indicate here the input file
process.source.fileNames=cms.untracked.vstring('file:singleTopEdmNtuple_TChannel.root')
#process.source.fileNames=cms.untracked.vstring('file:edmNtupleTest.root')

### Indicate here the number of events on which perform the selection
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )


import HLTrigger.HLTfilters.hltHighLevel_cfi
process.HLTFilter = HLTrigger.HLTfilters.hltHighLevel_cfi.hltHighLevel.clone()

process.HLTFilter.HLTPaths  = ["HLT_Ele27_WP80_v*", "HLT_IsoMu24_v*" ]



process.triggerFilter = cms.Path(
         process.HLTFilter
            )


process.edmNtuplesOut = cms.OutputModule(
    "PoolOutputModule",
    fileName = cms.untracked.string('tH_edmntuples.root'),
    outputCommands = cms.untracked.vstring(
    "keep *",
    "drop *_TriggerResults_*_PAT",
    "drop *_TriggerResults_*_NTPFILT",
    )
    )

process.edmNtuplesOut.SelectEvents = cms.untracked.PSet(
        SelectEvents = cms.vstring('triggerFilter')
            )

process.edmNtuplesOut.dropMetaData = cms.untracked.string('ALL')

process.endPath = cms.EndPath(process.edmNtuplesOut)