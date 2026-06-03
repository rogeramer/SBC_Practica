import math
from datetime import date, timedelta

from chatbot.recommendation_config import (
    ALLOW_UNRELEASED_MARKERS,
    COOP_SUPPORT_TAGS,
    GENRE_LABELS,
    ONLY_UNRELEASED_MARKERS,
    PLATFORM_LABELS,
    PROFILE_TO_RAWG,
    STRICT_TAGS,
    TAG_REASON_LABELS,
)

class RecommendationEngine:

    def __init__(self, rawg_service):
        self.rawg = rawg_service

    def _as_list(self, value):
        return value if isinstance(value, list) else []

    def _split_csv_values(self, value):
        if not value:
            return set()
        if isinstance(value, str):
            return {
                item.strip().lower()
                for item in value.split(",")
                if item.strip()
            }
        return {
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        }

    def _get_game_genres(self, game):
        return {
            genre.get("slug", "").lower()
            for genre in self._as_list(
                game.get("genres")
            )
            if (
                    isinstance(genre, dict)
                    and genre.get("slug")
            )
        }

    def _get_game_tags(self, game):
        return {
            tag.get("slug", "").lower()
            for tag in self._as_list(
                game.get("tags")
            )
            if (
                    isinstance(tag, dict)
                    and tag.get("slug")
            )
        }

    def _get_game_platform_ids(self, game):
        platform_ids = set()
        platform_groups = [
            self._as_list(
                game.get("platforms")
            ),
            self._as_list(
                game.get("parent_platforms")
            ),
        ]
        for group in platform_groups:
            for item in group:
                if not isinstance(item, dict):
                    continue
                platform_data = (
                        item.get("platform")
                        or {}
                )
                platform_id = platform_data.get(
                    "id"
                )
                if platform_id is not None:
                    platform_ids.add(
                        platform_id
                    )
        return platform_ids

    def _get_release_date(self, game):
        released = game.get("released")
        if not released:
            return None
        try:
            return date.fromisoformat(released)
        except ValueError:
            return None

    def _is_released_game(self, game):
        release_date = self._get_release_date(game)
        return (
            release_date is not None
            and release_date <= date.today()
        )

    def _is_upcoming_game(self, game):
        release_date = self._get_release_date(game)
        if release_date is None:
            return True

        return release_date > date.today()

    def _contains_marker(self, text, markers):
        return any(
            marker in text
            for marker in markers
        )

    def _get_release_mode(self, clean_text):
        allow_mixed_releases = self._contains_marker(
            clean_text,
            ALLOW_UNRELEASED_MARKERS,
        )
        only_unreleased = (
            not allow_mixed_releases
            and self._contains_marker(
                clean_text,
                ONLY_UNRELEASED_MARKERS,
            )
        )
        allow_unreleased = (
            only_unreleased
            or allow_mixed_releases
        )
        return {
            "allow_unreleased": allow_unreleased,
            "only_unreleased": only_unreleased,
            "allow_mixed_releases": allow_mixed_releases,
        }

    def _label_genre(self, slug):
        return GENRE_LABELS.get(
            slug,
            slug.replace("-", " "),
        )

    def _label_platforms(self, platform_ids):
        labels = [
            PLATFORM_LABELS.get(platform_id)
            for platform_id in platform_ids
            if PLATFORM_LABELS.get(platform_id)
        ]
        return ", ".join(
            sorted(labels)
        )

    def _append_reason(self, reasons, reason):
        if reason and reason not in reasons:
            reasons.append(reason)

    def _coop_tier(self, game_tags):
        if "co-op" not in game_tags:
            return 0

        if COOP_SUPPORT_TAGS.intersection(
            game_tags
        ):
            return 2

        return 1

    def build_request(
        self,
        clean_text,
        filters,
        context,
        profile=None,
    ):
        profile_params = (
            PROFILE_TO_RAWG.get(
                profile,
                {},
            )
            if profile
            else {}
        )

        explicit_genres = set(
            context.get(
                "genres",
                [],
            )
        ).union(
            filters.get("genres")
            or []
        )

        explicit_tags = set(
            context.get(
                "tags",
                [],
            )
        ).union(
            filters.get("tags")
            or []
        )

        explicit_platforms = set(
            context.get(
                "platforms",
                [],
            )
        ).union(
            filters.get("platforms")
            or []
        )

        profile_genres = self._split_csv_values(
            profile_params.get("genres")
        )

        profile_tags = self._split_csv_values(
            profile_params.get("tags")
        )

        release_mode = self._get_release_mode(
            clean_text
        )
        dates = filters.get("dates")

        if (release_mode["only_unreleased"] and not dates):
            tomorrow = (
                    date.today()
                    + timedelta(days=1)
            )
            future_limit = (
                    date.today()
                    + timedelta(days=365 * 4)
            )

            dates = (
                f"{tomorrow.isoformat()},"
                f"{future_limit.isoformat()}"
            )

        if dates:
            dates = str(dates).strip().replace("}", "")

        return {
            "search": filters.get("search"),
            "explicit_genres": explicit_genres,
            "explicit_tags": explicit_tags,
            "explicit_platforms": explicit_platforms,
            "profile_genres": profile_genres,
            "profile_tags": profile_tags,
            "ordering": (
                "released"
                if release_mode["only_unreleased"]
                else (
                    filters.get("ordering")
                    or context.get("ordering")
                    or "-added"
                )
            ),
            "dates": dates,
            "metacritic": (
                filters.get("metacritic")
                or context.get("metacritic")
            ),
            "allow_unreleased": release_mode[
                "allow_unreleased"
            ],
            "only_unreleased": release_mode[
                "only_unreleased"
            ],
            "allow_mixed_releases": release_mode[
                "allow_mixed_releases"
            ],
            "profile": profile,
        }

    def _merge_unique_games(
            self,
            *game_lists,
    ):
        merged = {}
        for games in game_lists:
            for game in games or []:
                if not isinstance(game, dict):
                    continue
                key = (
                        game.get("slug")
                        or str(
                    game.get("id")
                    or ""
                )
                )
                if key:
                    merged[key] = game
        return list(
            merged.values()
        )

    def _search_pages(
            self,
            *,
            genres,
            tags,
            common_params,
            pages,
    ):
        collected_games = []
        for page in pages:
            try:
                result = self.rawg.search_games(
                    genres=genres,
                    tags=tags,
                    page=page,
                    **common_params,
                )
            except RuntimeError as error:
                if (
                        page > 1
                        and "HTTP 404" in str(error)
                ):
                    break
                raise
            collected_games = self._merge_unique_games(
                collected_games,
                result.get("results") or [],
            )
            if not result.get("next"):
                break
        return collected_games

    def fetch_candidates(
            self,
            request_data,
            page_size=40,
            pages=None,
    ):
        genres_for_api = (
                request_data["explicit_genres"]
                or request_data["profile_genres"]
        )

        tags_for_api = (
                request_data["explicit_tags"]
                or request_data["profile_tags"]
        )

        platforms_for_api = request_data[
            "explicit_platforms"
        ]

        common_params = {
            "search": request_data["search"],
            "platforms": (
                ",".join(
                    str(value)
                    for value in platforms_for_api
                )
                if platforms_for_api
                else None
            ),
            "ordering": request_data["ordering"],
            "dates": request_data["dates"],
            "metacritic": request_data[
                "metacritic"
            ],
            "page_size": page_size,
        }

        genres = (
            ",".join(
                sorted(genres_for_api)
            )
            if genres_for_api
            else None
        )

        tags = (
            ",".join(
                sorted(tags_for_api)
            )
            if tags_for_api
            else None
        )

        pages_to_fetch = pages

        if pages_to_fetch is None:
            pages_to_fetch = (
                [1, 2]
                if (
                        "co-op" in request_data["explicit_tags"]
                        or request_data["only_unreleased"]
                )
                else [1]
            )

        if isinstance(
                pages_to_fetch,
                int,
        ):
            pages_to_fetch = [
                pages_to_fetch
            ]

        collected_games = self._search_pages(
            genres=genres,
            tags=tags,
            common_params=common_params,
            pages=pages_to_fetch,
        )

        if (
                tags
                and len(collected_games) < 25
        ):
            expanded_games = self._search_pages(
                genres=genres,
                tags=None,
                common_params=common_params,
                pages=pages_to_fetch,
            )

            collected_games = (
                self._merge_unique_games(
                    collected_games,
                    expanded_games,
                )
            )

        if (
                genres
                and len(collected_games) < 25
        ):
            broad_games = self._search_pages(
                genres=None,
                tags=None,
                common_params=common_params,
                pages=[1],
            )

            collected_games = (
                self._merge_unique_games(
                    collected_games,
                    broad_games,
                )
            )

        return collected_games

    def _matches_mandatory_constraints(
        self,
        game,
        request_data,
    ):

        game_genres = self._get_game_genres(
            game
        )

        game_tags = self._get_game_tags(
            game
        )

        game_platforms = (
            self._get_game_platform_ids(
                game
            )
        )

        explicit_genres = request_data[
            "explicit_genres"
        ]

        explicit_tags = request_data[
            "explicit_tags"
        ]

        explicit_platforms = request_data[
            "explicit_platforms"
        ]

        if (
            explicit_genres
            and not explicit_genres.issubset(
                game_genres
            )
        ):
            return False

        if (
            explicit_platforms
            and not explicit_platforms.intersection(
                game_platforms
            )
        ):
            return False

        requested_strict_tags = (
            explicit_tags.intersection(
                STRICT_TAGS
            )
        )

        if (
            requested_strict_tags
            and not requested_strict_tags.issubset(
                game_tags
            )
        ):
            return False

        if (
            "co-op" in explicit_tags
            and "co-op" not in game_tags
        ):
            return False

        if "multiplayer" in explicit_tags:
            if not {
                "multiplayer",
                "co-op",
            }.intersection(
                game_tags
            ):
                return False

        if request_data["only_unreleased"]:
            if not self._is_upcoming_game(game):
                return False

        elif not request_data[
            "allow_unreleased"
        ]:
            if not self._is_released_game(game):
                return False

        return True


    def _build_natural_reasons(
        self,
        *,
        game,
        request_data,
    ):

        reasons = []

        game_genres = self._get_game_genres(
            game
        )

        game_tags = self._get_game_tags(
            game
        )

        game_platforms = (
            self._get_game_platform_ids(
                game
            )
        )

        explicit_genres = request_data[
            "explicit_genres"
        ]

        explicit_tags = request_data[
            "explicit_tags"
        ]

        profile_tags = request_data[
            "profile_tags"
        ]

        matched_genres = (
            explicit_genres.intersection(
                game_genres
            )
        )

        if matched_genres:
            readable_genres = ", ".join(
                sorted(
                    self._label_genre(
                        genre
                    )
                    for genre in matched_genres
                )
            )

            self._append_reason(
                reasons,
                (
                    "pertenece al género "
                    f"{readable_genres}"
                ),
            )

        ignored_reason_tags = {
            "rpg",
        }

        matched_explicit_tags = (
            explicit_tags.intersection(
                game_tags
            )
            - ignored_reason_tags
        )

        matched_explicit_tags.discard(
            "co-op"
        )

        for tag in sorted(
            matched_explicit_tags
        ):
            label = TAG_REASON_LABELS.get(
                tag
            )

            if label:
                self._append_reason(
                    reasons,
                    label,
                )

        if "co-op" in explicit_tags:
            coop_tier = self._coop_tier(
                game_tags
            )

            if coop_tier == 2:
                self._append_reason(
                    reasons,
                    (
                        "ofrece cooperativo "
                        "local u online"
                    ),
                )

            elif coop_tier == 1:
                self._append_reason(
                    reasons,
                    "incluye un modo cooperativo",
                )

        matched_profile_tags = (
            profile_tags.intersection(
                game_tags
            )
            - explicit_tags
            - ignored_reason_tags
        )

        for tag in sorted(
            matched_profile_tags
        ):
            label = TAG_REASON_LABELS.get(
                tag
            )

            if label:
                self._append_reason(
                    reasons,
                    label,
                )

        if request_data[
            "explicit_platforms"
        ]:
            if request_data[
                "explicit_platforms"
            ].intersection(
                game_platforms
            ):
                readable_platforms = (
                    self._label_platforms(
                        request_data[
                            "explicit_platforms"
                        ]
                    )
                )
                self._append_reason(
                    reasons,
                    (
                        "está disponible en "
                        f"{readable_platforms}"
                    ),
                )

        if request_data["only_unreleased"]:
            release_date = (
                self._get_release_date(game)
            )

            if release_date:
                self._append_reason(
                    reasons,
                    "es un próximo lanzamiento",
                )

            else:
                self._append_reason(
                    reasons,
                    (
                        "todavía no tiene una "
                        "fecha confirmada"
                    ),
                )

        return reasons[:3]


    def _calculate_game_score(
        self,
        game,
        request_data,
    ):
        score = 0.0

        game_genres = self._get_game_genres(
            game
        )

        game_tags = self._get_game_tags(
            game
        )

        game_platforms = (
            self._get_game_platform_ids(
                game
            )
        )

        explicit_genres = request_data[
            "explicit_genres"
        ]

        explicit_tags = request_data[
            "explicit_tags"
        ]

        profile_genres = request_data[
            "profile_genres"
        ]

        profile_tags = request_data[
            "profile_tags"
        ]

        effective_explicit_tags = (
            explicit_tags - {"rpg"}
        )

        score += 12 * len(
            explicit_genres.intersection(
                game_genres
            )
        )

        score += 10 * len(
            effective_explicit_tags.intersection(
                game_tags
            )
        )

        score += 5 * len(
            profile_genres.intersection(
                game_genres
            )
        )

        score += 4 * len(
            profile_tags.intersection(
                game_tags
            )
        )

        if request_data[
            "explicit_platforms"
        ].intersection(
            game_platforms
        ):
            score += 5

        if "co-op" in explicit_tags:
            coop_tier = self._coop_tier(
                game_tags
            )

            if coop_tier == 2:
                score += 20

            elif coop_tier == 1:
                score += 4

        if request_data["only_unreleased"]:
            release_date = (
                self._get_release_date(game)
            )

            score += (
                8
                if release_date
                else 2
            )

        rating = float(
            game.get("rating")
            or 0
        )

        ratings_count = int(
            game.get("ratings_count")
            or 0
        )

        added = int(
            game.get("added")
            or 0
        )

        metacritic = int(
            game.get("metacritic")
            or 0
        )

        score += rating * 1.5

        score += min(
            math.log1p(
                ratings_count
            ),
            8,
        ) * 1.2
        score += min(
            math.log1p(
                added
            ),
            10,
        ) * 0.8
        if metacritic:
            score += metacritic / 20
        if ratings_count < 20:
            score -= 5
        if ratings_count < 5:
            score -= 5
        reasons = (
            self._build_natural_reasons(
                game=game,
                request_data=request_data,
            )
        )
        return (
            round(
                score,
                2,
            ),
            reasons,
        )

    def rank_games(
        self,
        games,
        request_data,
        limit=5,
        excluded_slugs=None,
    ):
        excluded_slugs = set(
            excluded_slugs or []
        )
        ranked_games = []
        for game in games:
            if not isinstance(game, dict):
                continue
            game_slug = game.get("slug")
            if (
                game_slug
                and game_slug in excluded_slugs
            ):
                continue
            if not self._matches_mandatory_constraints(
                game,
                request_data,
            ):
                continue
            score, reasons = (
                self._calculate_game_score(
                    game,
                    request_data,
                )
            )
            enriched_game = dict(game)
            enriched_game[
                "_recommendation_score"
            ] = score
            enriched_game[
                "_recommendation_reasons"
            ] = reasons
            enriched_game[
                "_coop_tier"
            ] = self._coop_tier(
                self._get_game_tags(
                    game
                )
            )
            ranked_games.append(
                enriched_game
            )
        if (
            "co-op"
            in request_data[
                "explicit_tags"
            ]
        ):
            ranked_games.sort(
                key=lambda game: (
                    game.get(
                        "_coop_tier",
                        0,
                    ),
                    game.get(
                        "_recommendation_score",
                        0,
                    ),
                    game.get(
                        "ratings_count",
                        0,
                    ),
                    game.get(
                        "added",
                        0,
                    ),
                ),
                reverse=True,
            )
        else:
            ranked_games.sort(
                key=lambda game: (
                    game.get(
                        "_recommendation_score",
                        0,
                    ),
                    game.get(
                        "ratings_count",
                        0,
                    ),
                    game.get(
                        "added",
                        0,
                    ),
                ),
                reverse=True,
            )
        return ranked_games[:limit]