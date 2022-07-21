from .ggo import controllers as ggo
from .auth import controllers as auth
from .technologies import controllers as technology
from .measurements import controllers as measurements
from .meteringpoints import controllers as meteringpoints
from .agreements import controllers as agreements
from .support import controllers as support
from .commodities import controllers as commodities
from .facilities import controllers as facilities


urls = (

    # -- NEW -----------------------------------------------------------------

    # Users
    ('/users/signup', auth.Signup()),
    ('/users/login', auth.Login()),
    ('/users/profile', auth.GetProfile()),
    ('/users/autocomplete', auth.AutocompleteUsers()),

    # MeteringPoints
    ('/meteringpoints', meteringpoints.GetMeteringPointList()),
    ('/meteringpoints/details', meteringpoints.GetMeteringPointDetails()),

    # Measurements
    ('/measurements', measurements.GetMeasurementList()),
    ('/measurements/summary', measurements.GetMeasurementSummary()),

    # GGOs
    ('/ggo', ggo.GetGgoList()),
    ('/ggo/summary', ggo.GetGgoSummary()),
    ('/ggo/compose', ggo.ComposeGgo()),

    # Technologies
    ('/technologies', technology.GetTechnologies()),

    # Facilities
    ('/facilities', facilities.GetFacilityList()),
    ('/facilities/edit', facilities.EditFacilityDetails()),
    ('/facilities/get-filtering-options', facilities.GetFilteringOptions()),
    ('/facilities/set-retiring-priority', facilities.SetRetiringPriority()),
    # ('/facilities/retire-back-in-time', facilities.RetireBackInTime()),

    # Commodities
    ('/commodities/distributions', commodities.GetGgoDistributions()),
    ('/commodities/ggo-summary', commodities.GetGgoSummary()),
    ('/commodities/measurements', commodities.GetMeasurements()),
    ('/commodities/get-peak-measurement', commodities.GetPeakMeasurement()),

    # Agreements
    ('/agreements', agreements.GetAgreementList()),
    ('/agreements/details', agreements.GetAgreementDetails()),
    ('/agreements/summary', agreements.GetAgreementSummary()),
    ('/agreements/cancel', agreements.CancelAgreement()),
    ('/agreements/set-transfer-priority', agreements.SetTransferPriority()),
    ('/agreements/propose', agreements.SubmitAgreementProposal()),
    ('/agreements/propose/respond', agreements.RespondToProposal()),
    ('/agreements/propose/withdraw', agreements.WithdrawProposal()),
    ('/agreements/propose/pending-count', agreements.CountPendingProposals()),

    # Misc
    ('/support/submit-support-enquiry', support.SubmitSupportEnquiry()),

)
