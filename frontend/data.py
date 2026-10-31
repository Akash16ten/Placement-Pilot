"""Cached, failure-tolerant reads of the progress endpoints. Cache is keyed by (session, rev) and rev is bumped on every write."""
from __future__ import annotations

import streamlit as st

import api


@st.cache_data(ttl=120, show_spinner=False)
def _plan(sid: str, rev: int):
    return api.plan(sid)


@st.cache_data(ttl=120, show_spinner=False)
def _dash(sid: str, rev: int):
    return api.dashboard(sid)


@st.cache_data(ttl=20, show_spinner=False)
def _health():
    return api.health()


def plan(sid: str, rev: int):
    try:
        return _plan(sid, rev)
    except api.ApiError:
        return None


def dash(sid: str, rev: int):
    try:
        return _dash(sid, rev)
    except api.ApiError:
        return None


def health():
    try:
        return _health()
    except api.ApiError:
        return None
