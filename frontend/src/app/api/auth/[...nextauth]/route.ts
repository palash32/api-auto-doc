import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const authOptions = {
    providers: [
        CredentialsProvider({
            name: "Backend Token",
            credentials: {
                token: { label: "Token", type: "text" },
                user: { label: "User", type: "text" }, // JSON string of user data
            },
            async authorize(credentials) {
                if (credentials?.token && credentials?.user) {
                    try {
                        const user = JSON.parse(credentials.user);
                        return {
                            id: user.id,
                            name: user.full_name,
                            email: user.email,
                            image: user.avatar_url,
                            accessToken: credentials.token,
                            role: user.role,
                            organizationId: user.organization_id,
                        };
                    } catch (e) {
                        return null;
                    }
                }
                return null;
            },
        }),
    ],
    callbacks: {
        async jwt({ token, user }: { token: any; user?: any }) {
            if (user) {
                token.accessToken = user.accessToken;
                token.role = user.role;
                token.organizationId = user.organizationId;
            }
            return token;
        },
        async session({ session, token }: { session: any; token: any }) {
            session.accessToken = token.accessToken;
            session.user.role = token.role;
            session.user.organizationId = token.organizationId;
            return session;
        },
    },
    pages: {
        signIn: "/login",
    },
    session: {
        strategy: "jwt" as const,
    },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
