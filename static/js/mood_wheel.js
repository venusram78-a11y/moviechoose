const Picker = {
    selectedMood: null,
    selectedLang: 'any',
    currentTmdbId: null,
    _loadingInterval: null,

    LOADING_MESSAGES: [
        'Scanning Indian cinema...',
        'Matching your mood...',
        'Checking what streams in India...',
        'Almost there...',
        'Found something for you...',
    ],

    init() {
        // Mood buttons
        document.querySelectorAll('.mood-btn')
            .forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll(
                    '.mood-btn'
                ).forEach(b =>
                    b.classList.remove('selected')
                );
                btn.classList.add('selected');
                this.selectedMood = btn.dataset.mood;
                this.showStep('step-language');
            });
        });

        // Language buttons
        document.querySelectorAll('.lang-btn')
            .forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll(
                    '.lang-btn'
                ).forEach(b =>
                    b.classList.remove('active')
                );
                btn.classList.add('active');
                this.selectedLang = (
                    btn.dataset.lang || 'any'
                );
            });
        });

        // Pick button
        document.getElementById('pick-btn')
            ?.addEventListener('click', () => {
            if (!this.selectedMood) return;
            this.fetchPick();
        });

        // Not this film
        document.getElementById('btn-not-this')
            ?.addEventListener('click', () => {
            this.fetchPick();
        });

        // Pick again
        document.getElementById('btn-pick-again')
            ?.addEventListener('click', () => {
            this.selectedMood = null;
            this.selectedLang = 'any';
            document.querySelectorAll(
                '.mood-btn'
            ).forEach(b =>
                b.classList.remove('selected')
            );
            document.querySelectorAll(
                '.lang-btn'
            ).forEach(b =>
                b.classList.remove('active')
            );
            const anyBtn = document.querySelector(
                '.lang-btn[data-lang="any"]'
            );
            if (anyBtn) {
                anyBtn.classList.add('active');
            }
            this.showStep('step-mood');
        });

        // I watched this
        document.getElementById('btn-watched')
            ?.addEventListener('click', () => {
            if (!this.currentTmdbId) return;
            fetch('/pick/watched/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrf(),
                    'Content-Type':
                        'application/x-www-form-urlencoded',
                },
                body: `tmdb_id=${this.currentTmdbId}`,
            });
            const btn = document.getElementById(
                'btn-watched'
            );
            if (btn) {
                btn.textContent = '✓ Marked!';
                btn.style.background = (
                    'rgba(46,204,113,0.2)'
                );
                btn.disabled = true;
            }
        });

        // WhatsApp share
        document.getElementById('btn-share-wa')
            ?.addEventListener('click', () => {
            const text = window.currentShareText;
            const url = window.currentShareUrl;
            if (!text || !url) return;
            const full = text + '\n' + url;
            window.open(
                'https://wa.me/?text='
                + encodeURIComponent(full),
                '_blank',
                'noopener,noreferrer'
            );
        });

        // Trailer button
        document.getElementById('btn-trailer')
            ?.addEventListener('click', function() {
            const key = this.dataset.trailerKey;
            if (!key) return;
            const url = (
                `https://www.youtube.com/embed/${key}`
                + `?autoplay=1&rel=0`
            );
            const iframe = document.getElementById(
                'trailer-iframe'
            );
            if (iframe) iframe.src = url;
            const modal = new bootstrap.Modal(
                document.getElementById(
                    'trailerModal'
                )
            );
            modal.show();
        });

        // Stop trailer on modal close
        document.getElementById('trailerModal')
            ?.addEventListener(
                'hidden.bs.modal', () => {
            const iframe = document.getElementById(
                'trailer-iframe'
            );
            if (iframe) iframe.src = '';
        });

        // Report buttons
        document.querySelectorAll('.report-opt')
            .forEach(btn => {
            btn.addEventListener('click', () => {
                if (!this.currentTmdbId) return;
                fetch('/pick/report/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrf(),
                        'Content-Type':
                            'application/x-www-form-urlencoded',
                    },
                    body: (
                        `tmdb_id=${this.currentTmdbId}`
                        + `&reason=${btn.dataset.reason}`
                    ),
                });
                const opts = document.getElementById(
                    'report-options'
                );
                const thanks = document.getElementById(
                    'report-thanks'
                );
                if (opts) opts.style.display = 'none';
                if (thanks) {
                    thanks.style.display = 'block';
                }
            });
        });
    },

    async fetchPick() {
        if (!this.selectedMood) return;

        this.showStep('step-loading');
        this.animateLoadingText();

        try {
            const resp = await fetch('/pick/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrf(),
                    'Content-Type':
                        'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    mood: this.selectedMood,
                    language: this.selectedLang,
                }),
            });

            if (this._loadingInterval) {
                clearInterval(this._loadingInterval);
                this._loadingInterval = null;
            }

            if (resp.status === 403) {
                this.showSessionExpired();
                return;
            }

            if (!resp.ok) {
                const err = await resp.json().catch(
                    () => ({})
                );
                this.showError(
                    err.error
                    || 'Could not find a film. '
                    + 'Try a different mood!'
                );
                return;
            }

            const data = await resp.json();
            if (!data.title) {
                this.showError(
                    'No film found. Try a different mood!'
                );
                return;
            }

            this.displayResult(data);

        } catch (e) {
            if (this._loadingInterval) {
                clearInterval(this._loadingInterval);
                this._loadingInterval = null;
            }
            this.showError(
                'Connection issue. Please try again.'
            );
        }
    },

    displayResult(data) {
        this.currentTmdbId = data.tmdb_id;
        window.currentShareText = (
            data.whatsapp_share_text || ''
        );
        window.currentShareUrl = (
            data.share_url
            || `https://moviechoose.com/pick/${data.tmdb_id}/`
        );

        // Poster
        const poster = document.getElementById(
            'result-poster'
        );
        if (poster) {
            poster.alt = data.title || '';
            poster.onerror = function() {
                this.onerror = null;
                this.src = '/static/images/no-poster.jpg';
            };
            poster.src = (
                data.poster_url
                && data.poster_url.includes('tmdb.org')
            )
                ? data.poster_url
                : '/static/images/no-poster.jpg';
        }

        // Rating badge
        const rating = document.getElementById(
            'result-rating'
        );
        if (rating && data.vote_average) {
            rating.textContent = (
                '⭐ '
                + parseFloat(data.vote_average)
                    .toFixed(1)
            );
        }

        // Title
        const title = document.getElementById(
            'result-title'
        );
        if (title) title.textContent = data.title || '';

        // Mood echo
        const echo = document.getElementById(
            'result-mood-echo'
        );
        if (echo) {
            echo.textContent = (
                this.moodEmoji(this.selectedMood)
                + ' Perfect for your '
                + (this.selectedMood || '')
                + ' mood'
            );
        }

        // Meta
        const meta = document.getElementById(
            'result-meta'
        );
        if (meta) {
            const parts = [];
            if (data.release_year) {
                parts.push(data.release_year);
            }
            if (data.runtime) {
                parts.push(data.runtime + ' min');
            }
            if (data.language) {
                parts.push(
                    this.langLabel(data.language)
                );
            }
            meta.textContent = parts.join(' · ');
        }

        // Overview
        const overview = document.getElementById(
            'result-overview'
        );
        if (overview) {
            overview.textContent = data.overview || '';
        }

        // Genres
        const genresEl = document.getElementById(
            'result-genres'
        );
        if (genresEl) {
            const genres = data.genres || [];
            if (genres.length > 0) {
                genresEl.innerHTML = genres
                    .slice(0, 3)
                    .map(g =>
                        `<span class="genre-tag">${g}</span>`
                    )
                    .join('');
                genresEl.style.display = 'flex';
            } else {
                genresEl.style.display = 'none';
            }
        }

        // Streaming providers
        const streamEl = document.getElementById(
            'result-streaming'
        );
        if (streamEl) {
            const providers = (
                data.streaming_providers || []
            );
            const watchUrl = data.tmdb_watch_url || '';

            if (providers.length > 0) {
                const logosHTML = providers
                    .slice(0, 6)
                    .map(p => {
                        const logo = p.logo_url
                            ? `<img src="${p.logo_url}"
                                   alt="${p.name}"
                                   title="${p.name}"
                                   class="provider-logo"
                                   loading="lazy"
                                   onerror="this.parentElement
                                     .style.display='none'">`
                            : '';
                        return `<div class="provider-chip"
                                     title="${p.name}">
                                  ${logo}
                                  <span class="provider-name">
                                    ${p.name}
                                  </span>
                                </div>`;
                    })
                    .join('');

                streamEl.innerHTML = `
                    <div class="streaming-label">
                      Now streaming in India
                    </div>
                    <div class="provider-list">
                      ${logosHTML}
                    </div>
                    ${watchUrl
                        ? `<a href="${watchUrl}"
                              target="_blank"
                              rel="noopener noreferrer"
                              class="where-to-watch-link">
                              Full watch options →
                           </a>`
                        : ''
                    }
                `;
            } else {
                streamEl.innerHTML = `
                    <div class="streaming-label"
                         style="color:#555;">
                      Not on major Indian platforms
                    </div>
                    ${watchUrl
                        ? `<a href="${watchUrl}"
                              target="_blank"
                              rel="noopener noreferrer"
                              class="where-to-watch-link"
                              style="color:#666;">
                              Check availability on TMDB →
                           </a>`
                        : ''
                    }
                `;
            }
            streamEl.style.display = 'block';
        }

        // Trailer button
        const trailerBtn = document.getElementById(
            'btn-trailer'
        );
        if (trailerBtn) {
            if (data.trailer_key) {
                trailerBtn.style.display = (
                    'inline-flex'
                );
                trailerBtn.dataset.trailerKey = (
                    data.trailer_key
                );
            } else {
                trailerBtn.style.display = 'none';
            }
        }

        // Streak
        if (data.streak && data.streak > 1) {
            const streakEl = document.getElementById(
                'streak-display'
            );
            const countEl = document.getElementById(
                'streak-count'
            );
            if (streakEl && countEl) {
                countEl.textContent = data.streak;
                streakEl.style.display = 'inline-flex';
            }
        }

        // Reset watched button
        const watchedBtn = document.getElementById(
            'btn-watched'
        );
        if (watchedBtn) {
            watchedBtn.textContent = 'I Watched This!';
            watchedBtn.disabled = false;
            watchedBtn.style.background = 'transparent';
        }

        // Reset report modal
        const opts = document.getElementById(
            'report-options'
        );
        const thanks = document.getElementById(
            'report-thanks'
        );
        if (opts) opts.style.display = 'block';
        if (thanks) thanks.style.display = 'none';

        this.showStep('step-result');

        // Load alternatives after result shows
        setTimeout(() => this.loadAlternatives(), 500);
    },

    async loadAlternatives() {
        try {
            const resp = await fetch(
                '/pick/alternatives/',
                {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrf(),
                        'Content-Type':
                            'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        mood: this.selectedMood,
                        language: this.selectedLang,
                        current_pick_id: (
                            this.currentTmdbId || ''
                        ),
                    }),
                }
            );
            if (!resp.ok) return;

            const data = await resp.json();
            const alts = data.alternatives || [];

            if (alts.length >= 2) {
                const grid = document.getElementById(
                    'alternatives-grid'
                );
                if (!grid) return;
                grid.innerHTML = '';

                alts.forEach(movie => {
                    const div = document.createElement(
                        'div'
                    );
                    div.className = 'alt-card';
                    div.innerHTML = `
                        <img src="${movie.poster_url}"
                             alt="${movie.title}"
                             class="alt-poster"
                             loading="lazy"
                             onerror="this.src='/static/images/no-poster.jpg'">
                        <div class="alt-title">
                          ${movie.title}
                        </div>
                    `;
                    div.addEventListener('click', () => {
                        this.displayResult(movie);
                        window.scrollTo({
                            top: 0,
                            behavior: 'smooth',
                        });
                    });
                    grid.appendChild(div);
                });

                const altSection = document.getElementById(
                    'alternatives'
                );
                if (altSection) {
                    altSection.style.display = 'block';
                }
            }
        } catch (e) {
            // Alternatives are non-critical
        }
    },

    showStep(stepId) {
        document.querySelectorAll('.picker-step')
            .forEach(s => {
            s.style.display = 'none';
        });
        const el = document.getElementById(stepId);
        if (el) el.style.display = 'block';
    },

    showError(message) {
        this.showStep('step-language');
        const toast = document.createElement('div');
        toast.style.cssText = (
            'position:fixed;bottom:80px;left:50%;'
            + 'transform:translateX(-50%);'
            + 'background:#c0392b;color:white;'
            + 'padding:12px 20px;border-radius:8px;'
            + 'z-index:9999;font-size:13px;'
            + 'max-width:90%;text-align:center;'
        );
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    },

    showSessionExpired() {
        const card = document.getElementById(
            'picker-card'
        );
        if (card) {
            card.innerHTML = `
                <div style="text-align:center;
                            padding:40px 20px;">
                  <p style="color:#aaa;
                            font-size:15px;
                            margin-bottom:16px;">
                    Your session timed out.
                    Let's start fresh!
                  </p>
                  <button
                    onclick="window.location.reload()"
                    class="btn-pick-now"
                    style="max-width:200px;
                           margin:0 auto;
                           display:block;">
                    Pick Again
                  </button>
                </div>
            `;
        }
    },

    animateLoadingText() {
        const el = document.getElementById(
            'loading-text'
        );
        if (!el) return;
        let i = 0;
        el.textContent = this.LOADING_MESSAGES[0];
        el.style.transition = 'opacity 0.2s ease';

        this._loadingInterval = setInterval(() => {
            i++;
            if (i < this.LOADING_MESSAGES.length) {
                el.style.opacity = '0';
                setTimeout(() => {
                    el.textContent = (
                        this.LOADING_MESSAGES[i]
                    );
                    el.style.opacity = '1';
                }, 200);
            }
        }, 900);
    },

    moodEmoji(mood) {
        const map = {
            happy:     '😄',
            sad:       '😢',
            thrilled:  '⚡',
            romantic:  '🥰',
            mindblown: '🤯',
            inspired:  '🔥',
            scared:    '😱',
            bored:     '🥱',
        };
        return map[mood] || '🎬';
    },

    langLabel(code) {
        const map = {
            te: 'Telugu',
            hi: 'Hindi',
            ta: 'Tamil',
            ml: 'Malayalam',
            kn: 'Kannada',
            mr: 'Marathi',
            bn: 'Bengali',
            pa: 'Punjabi',
            en: 'English',
        };
        return map[code] || code.toUpperCase();
    },

    getCsrf() {
        return document.cookie
            .split('; ')
            .find(r => r.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    },
};

document.addEventListener(
    'DOMContentLoaded', () => Picker.init()
);
