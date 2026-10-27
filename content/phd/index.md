---
title: My PhD, in plain words
kicker: My PhD
description: Samhan's Industry PhD at UNSW Sydney with Ausgrid, explained for lay readers, with links to the open-source tools.
---
I am an Industry PhD student at UNSW Sydney, with Ausgrid as my industry partner.

## Context

Ausgrid is a distribution network service provider, a DNSP: the company that owns and maintains the poles, wires and substations that carry electricity to 1.8 million customers across Sydney, the Hunter and the Central Coast. My PhD focuses on improving electricity forecasting for distribution networks like Ausgrid. With better forecasting, a network can plan its infrastructure better and spend its capital more efficiently. In Ausgrid's case that spending is around $2.9 billion for 2024 to 2029.

Rooftop solar makes forecasting harder. What a network now has to forecast is net load: the electricity customers draw from the grid minus what their solar panels generate. On a sunny midday, net load can fall so far that a suburb pushes power back up the wires, which is called reverse power flow, and the lowest point of the day, the minimum demand, has become as important to plan for as the evening peak.

## What I work on

In addition to a literature review, my PhD works on four independent and complementary projects. All of them have their data, code and documentation made publicly available as open-source tools in the PyN (Python for Network) library.

**Literature review.** I read more than 150 journal articles, conference papers and industry reports and studied about a hundred papers on net-load forecasting in detail. Most introduce a new model and report that it beats the ones it was compared with; few test whether the advantage holds on other data, whether the result is stable, or whether the code is available. Those gaps became the tools below.

**PyNNLF, Python for Network: Net Load Forecasting.** An open-source framework that runs forecasting models through the same test on public datasets, reporting accuracy, stability and run time, so that models can be compared fairly and reproducibly. Presented at the IEEE Power and Energy Society (PES) Asia-Pacific Power and Energy Engineering Conference (APPEEC) 2025 in Auckland and published in its proceedings.
[Documentation](https://mssamhan31.github.io/PyNNLF/) · [Paper on IEEE Xplore](https://ieeexplore.ieee.org/abstract/document/11382069)

**PyNRPF, Python for Network: Reverse Power Flow.** A tool that detects and corrects substation readings where older monitoring equipment records exported solar as consumption, applied across more than 300 zone substations at Ausgrid. Accepted for the IEEE PES Australasian Universities Power Engineering Conference (AUPEC) 2026 in Hobart.
[Code on GitHub](https://github.com/mssamhan31/PyNRPF)

**PyNTLP, Python for Network: Tariff to Load Profile.** A tool that estimates how a tariff such as Ausgrid's Solar Sharer Offer, which gives customers free electricity in the middle of the day, changes the daily load profile, using the Adaptive Quantile Flexibility method. Accepted for the IEEE PES Innovative Smart Grid Technologies (ISGT) Asia 2026 conference in Wuhan.
[Code on GitHub](https://github.com/mssamhan31/PyNTLP)

**PyNMDF, Python for Network: Minimum Demand Forecasting.** The fourth project, in progress: a study of the factors that drive minimum demand and a model to forecast it. No public release yet.

## Where it has been presented

This research has been presented at the conferences and symposia below, including international IEEE PES conferences in Auckland, Wuhan and Hobart.

<!-- conferences -->

Awards along the way include first place in the Three Minute Thesis competition at the UNSW School of Photovoltaic and Renewable Energy Engineering, best presenter in the energy track of the Indonesian Students' International Conference, and the Digital GreenTalents Award from the German Federal Ministry of Research, Technology and Space, which funds a three-month research exchange in Germany.

## Who makes it possible

This PhD is supervised by Dr Baran Yildiz and Associate Professor Anna Bruce at UNSW, and by Dr Navid Haghdadi and Daniel Sim from the Ausgrid Demand Forecasting team. It is fully funded by the University International Postgraduate Award from UNSW Sydney, with top-up scholarships from Ausgrid, RACE for 2030 and the NSW Decarbonisation Innovation Hub. Conference attendance has also been made possible by travel support from the UNSW Graduate Research School, the School of Photovoltaic and Renewable Energy Engineering, the Collaboration on Energy and Environmental Markets (CEEM), and my university supervisors.
